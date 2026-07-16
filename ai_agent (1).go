// AI Agent - Complete Autonomous Dev Server
// Features: OpenRouter Model Rotation, IDE APIs, Tool Calling, Memory, Streaming.

package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"time"
)

// ==========================================
// CONFIGURATION
// ==========================================

type Config struct {
	BaseURL string
	APIKey  string
	Models  []string
}

func loadConfig() Config {
	baseURL := os.Getenv("OPENAI_BASE_URL")
	if baseURL == "" {
		baseURL = "https://openrouter.ai/api/v1" // Default to OpenRouter
	}
	
	// Check for OpenRouter key first, fallback to OpenAI key if needed
	apiKey := os.Getenv("OPENROUTER_API_KEY")
	if apiKey == "" {
		apiKey = os.Getenv("OPENAI_API_KEY")
	}
	
	if apiKey == "" && !strings.Contains(baseURL, "localhost") {
		fmt.Println("Warning: OPENROUTER_API_KEY is not set. The agent will likely fail without it.")
	}
	
	modelsStr := os.Getenv("MODELS")
	if modelsStr == "" {
		// Default OpenRouter free models for automatic fallback rotation
		modelsStr = "meta-llama/llama-3.1-8b-instruct:free,google/gemma-2-9b-it:free,mistralai/mistral-7b-instruct:free,openchat/openchat-7b:free"
	}
	modelList := strings.Split(modelsStr, ",")
	for i := range modelList {
		modelList[i] = strings.TrimSpace(modelList[i])
	}

	return Config{
		BaseURL: baseURL,
		APIKey:  apiKey,
		Models:  modelList,
	}
}

// ==========================================
// OPENAI API TYPES
// ==========================================

type Message struct {
	Role       string      `json:"role"`
	Content    string      `json:"content,omitempty"`
	Name       string      `json:"name,omitempty"`
	ToolCallID string      `json:"tool_call_id,omitempty"`
	ToolCalls  []ToolCall  `json:"tool_calls,omitempty"`
}

type ToolCall struct {
	ID       string       `json:"id"`
	Type     string       `json:"type"`
	Function FunctionCall `json:"function"`
}

type FunctionCall struct {
	Name      string `json:"name"`
	Arguments string `json:"arguments"`
}

type Tool struct {
	Type     string               `json:"type"`
	Function ToolFunction         `json:"function"`
}

type ToolFunction struct {
	Name        string         `json:"name"`
	Description string         `json:"description"`
	Parameters  map[string]any `json:"parameters"`
}

type ChatRequest struct {
	Model       string    `json:"model"`
	Messages    []Message `json:"messages"`
	Tools       []Tool    `json:"tools,omitempty"`
	Stream      bool      `json:"stream,omitempty"`
	Temperature float32   `json:"temperature,omitempty"`
}

type ChatResponse struct {
	Choices []struct {
		Message      Message `json:"message"`
		FinishReason string  `json:"finish_reason"`
	} `json:"choices"`
}

type ChatStreamResponse struct {
	Choices []struct {
		Delta struct {
			Role      string     `json:"role,omitempty"`
			Content   string     `json:"content,omitempty"`
			ToolCalls []ToolCall `json:"tool_calls,omitempty"`
		} `json:"delta"`
		FinishReason *string `json:"finish_reason"`
	} `json:"choices"`
}

// ==========================================
// TOOL SYSTEM (Implementations)
// ==========================================

type ToolHandler func(args map[string]interface{}) (string, error)

var toolRegistry = map[string]ToolHandler{
	"read_file":      readFileTool,
	"write_file":     writeFileTool,
	"list_directory": listDirectoryTool,
	"search_files":   searchFilesTool,
	"execute_shell":  executeShellTool,
}

var toolDefinitions = []Tool{
	{
		Type: "function",
		Function: ToolFunction{
			Name:        "read_file",
			Description: "Reads the content of a file at the specified path.",
			Parameters: map[string]any{
				"type": "object",
				"properties": map[string]any{"path": map[string]any{"type": "string"}},
				"required": []string{"path"},
			},
		},
	},
	{
		Type: "function",
		Function: ToolFunction{
			Name:        "write_file",
			Description: "Writes content to a file, creating it if it doesn't exist.",
			Parameters: map[string]any{
				"type": "object",
				"properties": map[string]any{
					"path":    map[string]any{"type": "string"},
					"content": map[string]any{"type": "string"},
				},
				"required": []string{"path", "content"},
			},
		},
	},
	{
		Type: "function",
		Function: ToolFunction{
			Name:        "list_directory",
			Description: "Lists files and folders in a directory.",
			Parameters: map[string]any{
				"type": "object",
				"properties": map[string]any{"path": map[string]any{"type": "string"}},
				"required": []string{"path"},
			},
		},
	},
	{
		Type: "function",
		Function: ToolFunction{
			Name:        "search_files",
			Description: "Searches for files containing a specific pattern.",
			Parameters: map[string]any{
				"type": "object",
				"properties": map[string]any{
					"dir":     map[string]any{"type": "string"},
					"pattern": map[string]any{"type": "string"},
				},
				"required": []string{"dir", "pattern"},
			},
		},
	},
	{
		Type: "function",
		Function: ToolFunction{
			Name:        "execute_shell",
			Description: "Executes a shell command on the server.",
			Parameters: map[string]any{
				"type": "object",
				"properties": map[string]any{"command": map[string]any{"type": "string"}},
				"required": []string{"command"},
			},
		},
	},
}

func readFileTool(args map[string]interface{}) (string, error) {
	path, ok := args["path"].(string)
	if !ok { return "", fmt.Errorf("missing path") }
	content, err := os.ReadFile(path)
	if err != nil { return "", err }
	return string(content), nil
}

func writeFileTool(args map[string]interface{}) (string, error) {
	path, ok := args["path"].(string)
	if !ok { return "", fmt.Errorf("missing path") }
	content, ok := args["content"].(string)
	if !ok { return "", fmt.Errorf("missing content") }
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil { return "", err }
	if err := os.WriteFile(path, []byte(content), 0644); err != nil { return "", err }
	return fmt.Sprintf("Successfully wrote %d bytes to %s", len(content), path), nil
}

func listDirectoryTool(args map[string]interface{}) (string, error) {
	path, ok := args["path"].(string)
	if !ok { return "", fmt.Errorf("missing path") }
	entries, err := os.ReadDir(path)
	if err != nil { return "", err }
	var sb strings.Builder
	for _, e := range entries {
		typ := "FILE"
		if e.IsDir() { typ = "DIR " }
		sb.WriteString(fmt.Sprintf("[%s] %s\n", typ, e.Name()))
	}
	if sb.Len() == 0 { return "Directory is empty.", nil }
	return sb.String(), nil
}

func searchFilesTool(args map[string]interface{}) (string, error) {
	dir, ok := args["dir"].(string)
	if !ok { return "", fmt.Errorf("missing dir") }
	pattern, ok := args["pattern"].(string)
	if !ok { return "", fmt.Errorf("missing pattern") }

	var results []string
	filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err == nil && !info.IsDir() && strings.Contains(info.Name(), pattern) {
			results = append(results, path)
		}
		return nil
	})
	if len(results) == 0 { return "No matching files.", nil }
	return strings.Join(results, "\n"), nil
}

func executeShellTool(args map[string]interface{}) (string, error) {
	command, ok := args["command"].(string)
	if !ok { return "", fmt.Errorf("missing command") }
	var cmd *exec.Cmd
	if runtime.GOOS == "windows" {
		cmd = exec.Command("cmd", "/c", command)
	} else {
		cmd = exec.Command("sh", "-c", command)
	}
	out, err := cmd.CombinedOutput()
	res := string(out)
	if err != nil { res += fmt.Sprintf("\nError: %v", err) }
	if res == "" { res = "Success with no output." }
	return res, nil
}

// ==========================================
// AI AGENT CORE
// ==========================================

type Agent struct {
	Config Config
	Client *http.Client
	Memory []Message
	mu     sync.Mutex
}

func NewAgent(cfg Config) *Agent {
	systemPrompt := `You are an expert autonomous AI developer agent. 
You can understand goals, explore file systems, read code, execute shell commands, and write solutions.
When asked to perform a task:
1. THINK step-by-step.
2. USE TOOLS to gather context if needed.
3. WRITE or MODIFY files to achieve the goal.
4. Provide a brief summary of what you did when finished.`

	return &Agent{
		Config: cfg,
		Client: &http.Client{Timeout: 120 * time.Second},
		Memory: []Message{{Role: "system", Content: systemPrompt}},
	}
}

func (a *Agent) Run(userPrompt string, sendChunk func(string)) {
	a.Memory = append(a.Memory, Message{Role: "user", Content: userPrompt})

	for {
		req := ChatRequest{
			Messages:    a.Memory,
			Tools:       toolDefinitions,
			Stream:      true,
			Temperature: 0.2,
		}

		responseMsg, err := a.streamCompletion(req, sendChunk)
		if err != nil {
			sendChunk(fmt.Sprintf("\n[Error: %v]\n", err))
			break
		}

		a.Memory = append(a.Memory, responseMsg)

		if len(responseMsg.ToolCalls) > 0 {
			for _, tc := range responseMsg.ToolCalls {
				sendChunk(fmt.Sprintf("\n\n> **🛠️ Executing Tool:** `%s`\n\n", tc.Function.Name))
				fmt.Printf("  [🛠️ Executing Tool: %s]\n", tc.Function.Name)
				
				var args map[string]interface{}
				if err := json.Unmarshal([]byte(tc.Function.Arguments), &args); err != nil {
					a.appendToolError(tc.ID, fmt.Sprintf("Arg parse error: %v", err))
					continue
				}

				handler, exists := toolRegistry[tc.Function.Name]
				if !exists { continue }

				result, err := handler(args)
				if err != nil {
					a.appendToolError(tc.ID, fmt.Sprintf("Error: %v", err))
					sendChunk(fmt.Sprintf("\n> **❌ Tool Error:** `%v`\n\n", err))
				} else {
					a.Memory = append(a.Memory, Message{
						Role: "tool", Content: result, ToolCallID: tc.ID, Name: tc.Function.Name,
					})
					sendChunk("\n> **✅ Tool Success**\n\n")
				}
			}
			continue // Send tool results back to LLM
		}
		break
	}
}

func (a *Agent) appendToolError(toolID, errMsg string) {
	a.Memory = append(a.Memory, Message{Role: "tool", Content: errMsg, ToolCallID: toolID})
}

func (a *Agent) streamCompletion(req ChatRequest, sendChunk func(string)) (Message, error) {
	var lastErr error

	for i, modelName := range a.Config.Models {
		req.Model = modelName
		reqBody, _ := json.Marshal(req)
		url := fmt.Sprintf("%s/chat/completions", strings.TrimRight(a.Config.BaseURL, "/"))
		
		httpReq, _ := http.NewRequest("POST", url, bytes.NewBuffer(reqBody))
		httpReq.Header.Set("Content-Type", "application/json")
		httpReq.Header.Set("Authorization", "Bearer "+a.Config.APIKey)
		httpReq.Header.Set("Accept", "text/event-stream")
		httpReq.Header.Set("HTTP-Referer", "https://github.com/railwayapp")
		httpReq.Header.Set("X-Title", "Go AI Agent")

		resp, err := a.Client.Do(httpReq)
		if err != nil {
			lastErr = err
			if i < len(a.Config.Models)-1 {
				sendChunk(fmt.Sprintf("\n> ⚠️ Network error on `%s`. Rotating...\n\n", modelName))
				continue
			}
		}

		if resp != nil && resp.StatusCode != http.StatusOK {
			body, _ := io.ReadAll(resp.Body)
			if resp != nil { resp.Body.Close() }
			lastErr = fmt.Errorf("API error %d: %s", resp.StatusCode, string(body))
			
			// 429 Rate Limit or 5xx Server Error -> Rotate Model
			if i < len(a.Config.Models)-1 {
				sendChunk(fmt.Sprintf("\n> ⚠️ Model `%s` exhausted (Status %d). Rotating to next...\n\n", modelName, resp.StatusCode))
				continue
			} else {
				return Message{}, lastErr
			}
		}

		// Connection successful, process stream
		defer resp.Body.Close()
		reader := bufio.NewReader(resp.Body)
		finalMessage := Message{Role: "assistant"}
		
		for {
			line, err := reader.ReadString('\n')
			if err != nil {
				if err == io.EOF { break }
				return finalMessage, err
			}

			line = strings.TrimSpace(line)
			if line == "" || line == "data: [DONE]" {
				if line == "data: [DONE]" { break }
				continue
			}

			if strings.HasPrefix(line, "data: ") {
				data := strings.TrimPrefix(line, "data: ")
				var streamResp ChatStreamResponse
				if err := json.Unmarshal([]byte(data), &streamResp); err != nil { continue }

				if len(streamResp.Choices) > 0 {
					delta := streamResp.Choices[0].Delta
					
					if delta.Content != "" {
						sendChunk(delta.Content)
						finalMessage.Content += delta.Content
					}

					for _, tc := range delta.ToolCalls {
						if len(finalMessage.ToolCalls) == 0 && tc.ID != "" {
							finalMessage.ToolCalls = append(finalMessage.ToolCalls, ToolCall{
								ID: tc.ID, Type: "function", Function: FunctionCall{Name: tc.Function.Name},
							})
						}
						if len(finalMessage.ToolCalls) > 0 && tc.Function.Arguments != "" {
							finalMessage.ToolCalls[0].Function.Arguments += tc.Function.Arguments
						}
					}
				}
			}
		}
		return finalMessage, nil // Successfully finished stream
	}
	return Message{}, fmt.Errorf("All models failed. Last error: %v", lastErr)
}

// ==========================================
// HTTP SERVER & MAIN
// ==========================================

var globalAgent *Agent

func setupCORS(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
}

func filesHandler(w http.ResponseWriter, r *http.Request) {
	setupCORS(w, r)
	if r.Method == "OPTIONS" { return }

	type FileInfo struct {
		Name  string `json:"name"`
		Path  string `json:"path"`
		IsDir bool   `json:"isDir"`
	}
	
	var files []FileInfo
	entries, err := os.ReadDir(".")
	if err == nil {
		for _, e := range entries {
			if strings.HasPrefix(e.Name(), ".") || e.Name() == "node_modules" { continue }
			files = append(files, FileInfo{Name: e.Name(), Path: e.Name(), IsDir: e.IsDir()})
		}
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(files)
}

func readFileHandler(w http.ResponseWriter, r *http.Request) {
	setupCORS(w, r)
	if r.Method == "OPTIONS" { return }

	path := r.URL.Query().Get("path")
	if path == "" { http.Error(w, "missing path", http.StatusBadRequest); return }

	content, err := os.ReadFile(path)
	if err != nil { http.Error(w, err.Error(), http.StatusInternalServerError); return }
	w.Write(content)
}

func terminalHandler(w http.ResponseWriter, r *http.Request) {
	setupCORS(w, r)
	if r.Method == "OPTIONS" { return }

	var req struct{ Command string `json:"command"` }
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil { return }

	var cmd *exec.Cmd
	if runtime.GOOS == "windows" {
		cmd = exec.Command("cmd", "/c", req.Command)
	} else {
		cmd = exec.Command("sh", "-c", req.Command)
	}
	out, err := cmd.CombinedOutput()
	res := string(out)
	if err != nil { res += fmt.Sprintf("\n[Error]: %v", err) }

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"output": res})
}

func chatHandler(w http.ResponseWriter, r *http.Request) {
	setupCORS(w, r)
	if r.Method == "OPTIONS" { return }

	var reqBody struct{ Prompt string `json:"prompt"` }
	if err := json.NewDecoder(r.Body).Decode(&reqBody); err != nil { return }

	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")

	flusher, ok := w.(http.Flusher)
	if !ok { return }

	sendChunk := func(text string) {
		encoded, _ := json.Marshal(map[string]string{"text": text})
		fmt.Fprintf(w, "data: %s\n\n", string(encoded))
		flusher.Flush()
	}

	globalAgent.mu.Lock()
	defer globalAgent.mu.Unlock()

	globalAgent.Run(reqBody.Prompt, sendChunk)
	fmt.Fprintf(w, "data: [DONE]\n\n")
	flusher.Flush()
}

func main() {
	fmt.Println("=====================================================")
	fmt.Println("🚀 Autonomous AI Dev Agent (Railway Server Mode)")
	fmt.Println("=====================================================")
	
	cfg := loadConfig()
	fmt.Printf("Base URL: %s\n", cfg.BaseURL)
	fmt.Printf("Models:   %v\n", cfg.Models)
	fmt.Println("-----------------------------------------------------")

	globalAgent = NewAgent(cfg)
	port := os.Getenv("PORT")
	if port == "" { port = "8080" }

	http.HandleFunc("/api/chat", chatHandler)
	http.HandleFunc("/api/files", filesHandler)
	http.HandleFunc("/api/file/read", readFileHandler)
	http.HandleFunc("/api/terminal", terminalHandler)

	fmt.Printf("Server listening on 0.0.0.0:%s\n", port)
	if err := http.ListenAndServe("0.0.0.0:"+port, nil); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}