"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  MapPin,
  DollarSign,
  Cloud,
  Sparkles,
  Globe,
  Loader2,
  TrendingUp,
  Info,
  Brain,
  ChevronRight
} from "lucide-react";
import { cn } from "../../lib/utils";
import Lottie from "lottie-react";
import planeAnimation from "../lottie/plane.json";
import botAnimation from "../lottie/rpa.json";
import userAnimation from "../lottie/user.json";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ToolTrace {
  name: string;
  args: Record<string, unknown>;
  result: Record<string, unknown>;
}

interface ThinkingStep {
  tool: string;
  reason: string;
  params?: Record<string, unknown>;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  traces?: ToolTrace[];
  isStreaming?: boolean;
  thinking?: ThinkingStep[];
  isThinking?: boolean;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);

  // Initialize welcome message after mount to avoid hydration issues
  useEffect(() => {
    setMounted(true);
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content: "Hello! I'm your AI travel assistant. I can help you with weather updates, currency conversion, travel information, and trip planning. Where would you like to explore today?",
        timestamp: new Date(),
      },
    ]);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    const assistantMessageId = (Date.now() + 1).toString();
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isStreaming: true,
      traces: [],
    };

    setMessages((prev) => [...prev, assistantMessage]);
    setStreamingMessageId(assistantMessageId);

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8080";
      const response = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: input,
          history: messages.map((msg) => ({
            role: msg.role === "assistant" ? "model" : "user",
            parts: [{ text: msg.content }],
          })),
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("No response body");
      }

      let buffer = "";
      const traces: ToolTrace[] = [];
      const thinkingSteps: ThinkingStep[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") continue;

            try {
              const parsed = JSON.parse(data);

              if (parsed.type === "thinking") {
                // Handle thinking event
                const step: ThinkingStep = {
                  tool: parsed.tool,
                  reason: parsed.reason,
                  params: parsed.params
                };
                thinkingSteps.push(step);
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, thinking: [...thinkingSteps], isThinking: true }
                      : msg
                  )
                );
              } else if (parsed.type === "thinking_complete") {
                // Stop showing thinking animation
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, isThinking: false }
                      : msg
                  )
                );
              } else if (parsed.type === "text") {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: msg.content + parsed.content, isThinking: false }
                      : msg
                  )
                );
              } else if (parsed.type === "tool_start") {
                // Handle tool start
              } else if (parsed.type === "tool_complete") {
                traces.push(parsed);
              } else if (parsed.type === "traces") {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, traces: parsed.traces }
                      : msg
                  )
                );
              } else if (parsed.type === "error") {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: `Error: ${parsed.content}`, isStreaming: false, isThinking: false }
                      : msg
                  )
                );
              }
            } catch (e) {
              console.error("Failed to parse SSE data:", e);
            }
          }
        }
      }

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, isStreaming: false, traces }
            : msg
        )
      );
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: "Sorry, I encountered an error. Please try again.",
                isStreaming: false,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
      setStreamingMessageId(null);
    }
  };

  const getToolIcon = (toolName: string) => {
    switch (toolName) {
      case "weather_tool":
        return <Cloud className="w-4 h-4" />;
      case "currency_convert":
        return <DollarSign className="w-4 h-4" />;
      case "wikipedia_search":
        return <Globe className="w-4 h-4" />;
      default:
        return <Info className="w-4 h-4" />;
    }
  };

  const suggestedQuestions = [
    "What's the weather in Paris?",
    "Convert 1000 USD to EUR",
    "Tell me about the Eiffel Tower",
    "How much will $2000 last me in Japan?"
  ];

  // Show loading state while mounting to prevent hydration issues
  if (!mounted) {
    return (
      <div className="flex flex-col h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950">
        <div className="flex items-center justify-center h-full">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950">
      {/* Header */}
      <div className="border-b border-slate-800/50 backdrop-blur-sm bg-slate-900/50">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative w-12 h-12">
              <div className="absolute inset-0 bg-indigo-500/20 blur-xl"></div>
              <Lottie
                animationData={planeAnimation}
                loop={true}
                autoplay={true}
                className="w-12 h-12 relative"
              />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-100">AI Travel Assistant</h1>
              <p className="text-xs text-slate-400">Your intelligent travel companion</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-yellow-500 animate-pulse" />
            <span className="text-sm text-slate-400">Powered by Gemini</span>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.length === 1 && (
            <div className="mb-8">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {suggestedQuestions.map((question, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInput(question)}
                    className="p-3 text-left text-sm text-slate-300 bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-xl hover:bg-slate-800/70 hover:border-indigo-500/50 transition-all duration-200 group"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      {idx === 0 && <Cloud className="w-4 h-4 text-blue-400" />}
                      {idx === 1 && <DollarSign className="w-4 h-4 text-green-400" />}
                      {idx === 2 && <MapPin className="w-4 h-4 text-red-400" />}
                      {idx === 3 && <TrendingUp className="w-4 h-4 text-purple-400" />}
                    </div>
                    <p className="text-xs group-hover:text-slate-200 transition-colors">{question}</p>
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-3 animate-fade-in",
                message.role === "user" ? "justify-end" : "justify-start"
              )}
            >
              {message.role === "assistant" && (
                <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-600/20 flex items-center justify-center shadow-lg shadow-indigo-500/20 border border-indigo-500/30">
                  <Lottie
                    animationData={botAnimation}
                    loop={true}
                    autoplay={true}
                    className="w-8 h-8"
                  />
                </div>
              )}

              <div className={cn(
                "max-w-2xl px-4 py-3 rounded-2xl backdrop-blur",
                message.role === "user"
                  ? "bg-indigo-600/20 border border-indigo-500/30 text-slate-100"
                  : "bg-slate-800/50 border border-slate-700/50 text-slate-200"
              )}>
                {/* Thinking display */}
                {message.thinking && message.thinking.length > 0 && (
                  <div className="mb-3 p-3 bg-slate-900/30 rounded-lg border border-slate-700/30">
                    <div className="flex items-center gap-2 mb-2">
                      <Brain className="w-4 h-4 text-indigo-400 animate-pulse" />
                      <span className="text-xs text-indigo-400 font-medium">
                        {message.isThinking ? "Thinking..." : "Thought Process"}
                      </span>
                    </div>
                    <div className="space-y-1">
                      {message.thinking.map((step, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-xs text-slate-400">
                          <ChevronRight className="w-3 h-3 mt-0.5 flex-shrink-0 text-slate-600" />
                          <div>
                            <span className="text-slate-300">
                              {step.tool === "stop" ? "Finalizing response" :
                               step.tool === "weather" ? "Checking weather" :
                               step.tool === "currency" ? "Converting currency" :
                               step.tool === "wikipedia" ? "Searching information" :
                               `Using ${step.tool}`}
                            </span>
                            {step.reason && (
                              <span className="ml-1 text-slate-500">- {step.reason}</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
                      strong: ({children}) => <strong className="font-semibold text-slate-100">{children}</strong>,
                      em: ({children}) => <em className="italic">{children}</em>,
                      ul: ({children}) => <ul className="list-disc list-inside mb-3 space-y-2 ml-4">{children}</ul>,
                      ol: ({children}) => <ol className="list-decimal list-inside mb-3 space-y-2 ml-4">{children}</ol>,
                      li: ({children}) => (
                        <li className="text-slate-200">
                          <span>{children}</span>
                        </li>
                      ),
                      code: ({className, children, ...props}) => {
                        const match = /language-(\w+)/.exec(className || '');
                        return match ? (
                          <pre className="p-3 rounded-lg bg-slate-900/50 border border-slate-700/50 overflow-x-auto">
                            <code className={className} {...props}>
                              {children}
                            </code>
                          </pre>
                        ) : (
                          <code className="px-1 py-0.5 rounded bg-slate-800 text-indigo-300 text-xs" {...props}>
                            {children}
                          </code>
                        );
                      },
                      blockquote: ({children}) => <blockquote className="border-l-2 border-indigo-500 pl-3 italic">{children}</blockquote>,
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>

                {message.isStreaming && (
                  <span className="inline-flex ml-2">
                    <span className="animate-pulse">▊</span>
                  </span>
                )}

                {message.traces && message.traces.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-700/50">
                    <p className="text-xs text-slate-400 mb-2">Tools used:</p>
                    <div className="flex flex-wrap gap-2">
                      {message.traces.map((trace, idx) => (
                        <div
                          key={idx}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-slate-900/50 rounded-lg text-xs text-slate-300 border border-slate-700/50"
                        >
                          {getToolIcon(trace.name)}
                          <span>{trace.name.replace(/_/g, " ")}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {mounted && (
                  <div className="mt-2 text-xs text-slate-500">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                )}
              </div>

              {message.role === "user" && (
                <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-slate-700/50 to-slate-800/50 flex items-center justify-center border border-slate-600/50">
                  <Lottie
                    animationData={userAnimation}
                    loop={true}
                    autoplay={true}
                    className="w-7 h-7"
                  />
                </div>
              )}
            </div>
          ))}

          {isLoading && streamingMessageId && (
            <div className="flex gap-3 justify-start animate-slide-up">
              <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-600/20 flex items-center justify-center shadow-lg shadow-indigo-500/20 border border-indigo-500/30">
                <Lottie
                  animationData={botAnimation}
                  loop={true}
                  autoplay={true}
                  className="w-8 h-8"
                />
              </div>
              <div className="px-4 py-3 rounded-2xl bg-slate-800/50 border border-slate-700/50">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-800/50 backdrop-blur-sm bg-slate-900/50">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage();
            }}
            className="flex gap-3"
          >
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me about weather, currency, places, or travel planning..."
              disabled={isLoading}
              className="flex-1 px-4 py-3 bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/20 transition-all duration-200 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className={cn(
                "px-6 py-3 rounded-xl font-medium transition-all duration-200 flex items-center gap-2",
                isLoading || !input.trim()
                  ? "bg-slate-800/50 text-slate-500 cursor-not-allowed"
                  : "bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-500 hover:to-purple-500 shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40"
              )}
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
              <span className="hidden sm:inline">Send</span>
            </button>
          </form>

          <div className="mt-2 flex items-center justify-center gap-4 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <MapPin className="w-3 h-3" /> Places
            </span>
            <span className="flex items-center gap-1">
              <Cloud className="w-3 h-3" /> Weather
            </span>
            <span className="flex items-center gap-1">
              <DollarSign className="w-3 h-3" /> Currency
            </span>
            <span className="flex items-center gap-1">
              <Globe className="w-3 h-3" /> Wikipedia
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}