import React, { useState, useEffect, useRef } from 'react';
import { marked } from 'marked';

// Hardcoded backend URL - Hidden from the UI
const BASE_URL = "https://real-estate-lead-capture-agent-production.up.railway.app";

// Optional: Add your Gemini API key here to enable the 🧠 Review and 🎨 Asset tools in the UI
const GEMINI_API_KEY = "";

export default function App() {
  // File System State
  const [files, setFiles] = useState([]);
  const [currentFile, setCurrentFile] = useState({ path: '', content: 'Select a file from the explorer to view its contents.' });
  
  // Terminal State
  const [terminalHistory, setTerminalHistory] = useState([{ text: 'Welcome to the integrated server terminal.', isCommand: false }]);
  const [terminalInput, setTerminalInput] = useState('');
  
  // Agent Chat State
  const [chatMessages, setChatMessages] = useState([
    { 
      role: 'system', 
      content: '<strong>AI System Online.</strong><br/>I am connected to your workspace. Give me a task, and I will execute tools, read files, and write code automatically.', 
      isHtml: true 
    }
  ]);
  const [agentPrompt, setAgentPrompt] = useState('');
  const [isAgentThinking, setIsAgentThinking] = useState(false);
  
  // Tool States
  const [isReviewing, setIsReviewing] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  // Auto-scroll refs
  const terminalEndRef = useRef(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalHistory]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const refreshFiles = async () => {
    try {
      const res = await fetch(`${BASE_URL}/api/files`);
      if (!res.ok) throw new Error('Failed to load');
      const data = await res.json();
      setFiles(data || []);
    } catch (err) {
      console.error("File refresh error:", err);
    }
  };

  useEffect(() => {
    refreshFiles();
    // Auto-refresh directory every 10 seconds
    const interval = setInterval(refreshFiles, 10000);
    return () => clearInterval(interval);
  }, []);

  const openFile = async (path) => {
    try {
      setCurrentFile({ path, content: 'Loading...' });
      const res = await fetch(`${BASE_URL}/api/file/read?path=${encodeURIComponent(path)}`);
      if (!res.ok) throw new Error('Cannot read file');
      const text = await res.text();
      setCurrentFile({ path, content: text });
    } catch (err) {
      setCurrentFile({ path, content: `Error: ${err.message}` });
    }
  };

  const handleTerminalSubmit = async (e) => {
    e.preventDefault();
    const cmd = terminalInput.trim();
    if (!cmd) return;

    setTerminalInput('');
    setTerminalHistory(prev => [...prev, { text: `~/app$ ${cmd}`, isCommand: true }]);

    if (cmd === 'clear') {
      setTerminalHistory([]);
      return;
    }

    try {
      const res = await fetch(`${BASE_URL}/api/terminal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: cmd })
      });
      const data = await res.json();
      setTerminalHistory(prev => [...prev, { text: data.output || '(No output)', isCommand: false }]);
      refreshFiles(); // Refresh directory in case command altered files
    } catch (err) {
      setTerminalHistory(prev => [...prev, { text: `Error: ${err.message}`, isCommand: false }]);
    }
  };

  const handleAgentSubmit = async (e) => {
    e.preventDefault();
    const text = agentPrompt.trim();
    if (!text) return;

    setAgentPrompt('');
    setIsAgentThinking(true);

    // Add user message and a blank placeholder for the assistant's stream
    setChatMessages(prev => [
      ...prev,
      { role: 'user', content: text, isHtml: false },
      { role: 'assistant', content: '', isHtml: true, isTyping: true }
    ]);

    let fullResponse = "";

    try {
      const response = await fetch(`${BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: text })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        let lines = buffer.split('\n\n');
        buffer = lines.pop(); // Keep incomplete chunk in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.substring(6);
            if (dataStr === '[DONE]') break;
            try {
              const data = JSON.parse(dataStr);
              if (data.text) {
                fullResponse += data.text;
                
                // Update the last message (the assistant's response) with new content parsed via Markdown
                setChatMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    content: marked.parse(fullResponse)
                  };
                  return updated;
                });

                // If tool was successful, refresh the file directory instantly
                if(data.text.includes("Tool Success")) {
                  refreshFiles();
                }
              }
            } catch (err) { /* Ignore JSON parse errors on partial chunks */ }
          }
        }
      }
    } catch (err) {
      fullResponse += `\n\n**Connection Error:** ${err.message}`;
      setChatMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: marked.parse(fullResponse),
          isError: true
        };
        return updated;
      });
    } finally {
      setIsAgentThinking(false);
      setChatMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1].isTyping = false;
        return updated;
      });
      refreshFiles();
    }
  };

  const addSystemMessage = (title, markdownContent) => {
    setChatMessages(prev => [
      ...prev,
      {
        role: 'system',
        isHtml: true,
        content: `<strong>${title}</strong><br>${marked.parse(markdownContent)}`,
        customStyle: 'bg-purple-900/30 border-purple-800 text-purple-200'
      }
    ]);
  };

  const reviewWithGemini = async () => {
    if (!currentFile.content || !currentFile.path) {
      addSystemMessage("Notice", "Please open a file from the explorer first to review it.");
      return;
    }
    if (!GEMINI_API_KEY) {
      addSystemMessage("Notice", "Please add your GEMINI_API_KEY to the App.jsx file to use this feature.");
      return;
    }

    setIsReviewing(true);
    const systemPrompt = "You are an expert senior software engineer. Review the provided code, point out bugs, security issues, and suggest improvements. Use markdown styling.";
    const userQuery = `Review this file (${currentFile.path}):\n\n${currentFile.content}`;
    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key=${GEMINI_API_KEY}`;

    const payload = {
      contents: [{ parts: [{ text: userQuery }] }],
      systemInstruction: { parts: [{ text: systemPrompt }] }
    };

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const result = await response.json();
      const text = result.candidates?.[0]?.content?.parts?.[0]?.text || "No review generated.";
      addSystemMessage(`🧠 Gemini Code Review: ${currentFile.path}`, text);
    } catch (err) {
      addSystemMessage("Error", `Gemini API failed: ${err.message}`);
    } finally {
      setIsReviewing(false);
    }
  };

  const generateAssetWithGemini = async () => {
    const promptText = agentPrompt.trim();
    if (!promptText) {
      addSystemMessage("Notice", "Please type an image description in the 'Agent Command' box below, then click '🎨 Gen Asset'.");
      return;
    }
    if (!GEMINI_API_KEY) {
      addSystemMessage("Notice", "Please add your GEMINI_API_KEY to the App.jsx file to use this feature.");
      return;
    }

    setIsGenerating(true);
    const payload = { instances: { prompt: promptText }, parameters: { sampleCount: 1 } };
    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key=${GEMINI_API_KEY}`;

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const result = await response.json();
      if (result.predictions && result.predictions.length > 0 && result.predictions[0].bytesBase64Encoded) {
        const imageUrl = `data:image/png;base64,${result.predictions[0].bytesBase64Encoded}`;
        setChatMessages(prev => [
          ...prev,
          {
            role: 'system',
            isHtml: true,
            content: `<strong>🎨 Generated Asset: ${promptText}</strong><div class="mt-2 text-center"><img src="${imageUrl}" class="rounded shadow-lg max-w-full h-auto inline-block border border-purple-500/50" /></div>`,
            customStyle: 'bg-purple-900/30 border-purple-800 text-purple-200'
          }
        ]);
        setAgentPrompt('');
      } else {
        addSystemMessage("Error", "Failed to generate image. No bytes returned.");
      }
    } catch (err) {
      addSystemMessage("Error", `Imagen API failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="bg-gray-900 text-gray-300 h-screen flex flex-col overflow-hidden font-sans">
      
      {/* Header (No Backend URL input visible) */}
      <header className="h-12 bg-gray-950 border-b border-gray-800 flex items-center px-4 justify-between shrink-0">
        <div className="flex items-center space-x-2 text-white">
          <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path>
          </svg>
          <span className="font-semibold text-sm tracking-wide">Agent IDE Workspace</span>
        </div>
      </header>

      {/* Main Workspace */}
      <div className="flex flex-1 overflow-hidden">
        
        {/* Left Sidebar: Explorer */}
        <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
          <div className="h-8 flex items-center px-3 text-xs font-semibold uppercase tracking-wider text-gray-500 bg-gray-800/50">
            Explorer
            <button onClick={refreshFiles} className="ml-auto hover:text-white transition-colors" title="Refresh">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 text-sm space-y-1">
            {files.length === 0 ? (
              <div className="text-gray-500 px-2 py-1 text-xs italic">Directory is empty</div>
            ) : (
              files.map((f, i) => (
                <div key={i} 
                     onClick={() => !f.isDir && openFile(f.path)}
                     className="cursor-pointer hover:bg-gray-800 px-2 py-1.5 rounded flex items-center gap-2 truncate transition-colors select-none">
                  <span>{f.isDir ? '📁' : '📄'}</span> 
                  <span>{f.name}</span>
                </div>
              ))
            )}
          </div>
        </aside>

        {/* Center: Editor & Terminal */}
        <main className="flex-1 flex flex-col bg-gray-900 min-w-0">
          
          {/* Editor Tabs & Toolbar */}
          <div className="h-8 flex items-center px-3 border-b border-gray-800 text-xs text-gray-400 bg-gray-800/50 justify-between">
            <span className={`text-gray-300 bg-gray-800 px-3 py-1 rounded-t border-t border-l border-r border-gray-700 ${!currentFile.path && 'hidden'}`}>
              {currentFile.path || 'No file open'}
            </span>
            <div className="flex items-center space-x-3 text-[11px] font-medium text-purple-400/80">
              <button onClick={reviewWithGemini} disabled={isReviewing} className="hover:text-purple-300 transition-colors flex items-center gap-1 bg-purple-900/20 px-2 py-0.5 rounded border border-purple-800/50 shadow-sm disabled:opacity-50">
                {isReviewing ? '⏳ Reviewing...' : '🧠 Gemini Review'}
              </button>
              <button onClick={generateAssetWithGemini} disabled={isGenerating} className="hover:text-purple-300 transition-colors flex items-center gap-1 bg-purple-900/20 px-2 py-0.5 rounded border border-purple-800/50 shadow-sm disabled:opacity-50">
                {isGenerating ? '⏳ Generating...' : '🎨 Gen Asset'}
              </button>
            </div>
          </div>
          
          {/* Code Viewer */}
          <div className="flex-1 p-4 overflow-auto bg-[#0d1117] relative">
            <pre><code className="text-gray-300 font-mono text-sm whitespace-pre-wrap">{currentFile.content}</code></pre>
          </div>

          {/* Terminal */}
          <div className="h-64 border-t border-gray-800 bg-black flex flex-col">
            <div className="h-8 flex items-center px-3 border-b border-gray-800 text-xs text-gray-400 bg-gray-900">
              Terminal (Server Shell)
            </div>
            <div className="flex-1 overflow-y-auto p-2 font-mono text-[0.85rem] text-green-400">
              {terminalHistory.map((item, i) => (
                <div key={i} className={item.isCommand ? 'text-white mt-1' : 'text-gray-400 whitespace-pre-wrap'}>
                  {item.text}
                </div>
              ))}
              <div ref={terminalEndRef} />
            </div>
            <form onSubmit={handleTerminalSubmit} className="flex items-center px-2 pb-2 font-mono text-[0.85rem] text-green-400">
              <span className="mr-2">~/app$</span>
              <input 
                type="text" 
                value={terminalInput}
                onChange={(e) => setTerminalInput(e.target.value)}
                className="bg-transparent border-none outline-none text-gray-200 flex-grow" 
                autoComplete="off" 
                spellCheck="false" 
              />
            </form>
          </div>
        </main>

        {/* Right Sidebar: Agent Chat */}
        <aside className="w-[400px] border-l border-gray-800 flex flex-col bg-gray-900">
          <div className="h-8 flex items-center px-3 border-b border-gray-800 text-xs font-semibold tracking-wider text-gray-500 uppercase bg-gray-800/50">
            Agent Command
          </div>
          
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatMessages.map((msg, i) => (
              <div key={i} className={`text-sm rounded p-3 ${
                msg.role === 'user' 
                  ? 'bg-blue-900/40 border border-blue-800/50 text-gray-200' 
                  : msg.customStyle || 'text-gray-300 prose prose-invert max-w-none'
              } ${msg.isError ? 'text-red-400' : ''}`}>
                {msg.isHtml ? (
                  <div dangerouslySetInnerHTML={{ __html: msg.content }} className={msg.isTyping ? "after:content-['▌'] after:animate-pulse" : ""} />
                ) : (
                  <div>{msg.content}</div>
                )}
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          {/* Chat Input Box */}
          <div className="p-3 bg-gray-800 border-t border-gray-800">
            <form onSubmit={handleAgentSubmit} className="flex flex-col gap-2">
              <textarea 
                rows="2" 
                value={agentPrompt}
                onChange={(e) => setAgentPrompt(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAgentSubmit(e); } }}
                className="w-full bg-gray-900 border border-gray-700 text-white text-sm rounded p-2 focus:border-blue-500 outline-none resize-none placeholder-gray-500"
                placeholder="E.g., 'Initialize a basic HTML file in this directory'" 
                disabled={isAgentThinking}
                required
              />
              <button 
                type="submit" 
                disabled={isAgentThinking}
                className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium py-1.5 rounded transition-colors flex justify-center items-center">
                {isAgentThinking ? 'Agent is thinking...' : 'Execute Agent Task'}
              </button>
            </form>
          </div>
        </aside>

      </div>
      
      {/* Required CSS overrides for markdown formatting */}
      <style dangerouslySetInnerHTML={{__html: `
        .prose pre { background-color: #111827; padding: 0.75rem; border-radius: 0.375rem; overflow-x: auto; margin: 0.5rem 0; font-family: monospace; font-size: 0.85rem; border: 1px solid #374151;}
        .prose code { background-color: #374151; padding: 0.125rem 0.25rem; border-radius: 0.25rem; font-family: monospace; font-size: 0.85em;}
        .prose p { margin-bottom: 0.5rem; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #4b5563; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #6b7280; }
      `}} />
    </div>
  );
}
