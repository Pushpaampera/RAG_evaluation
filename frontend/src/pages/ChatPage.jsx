import { useEffect, useRef, useState } from "react";

import "./ChatPage.css";



import ReactMarkdown from "react-markdown";

import remarkGfm from "remark-gfm";



const API_BASE_URL = (

  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"

).replace(/\/+$/, "");



const MAX_QUESTION_LENGTH = 10000;



const WELCOME_MESSAGE = {

  id: "welcome",

  role: "assistant",

  content:

    "Welcome to DocuLens AI. Your documents, understood. Ask questions, " +

    "explore key details, or request a summary of your uploaded documents. " +

    "I'll help you find relevant information and show its sources when available.",

  time: formatTime(),

  sources: [],

  relevance: null,

  evaluation: undefined,

};



const EVALUATION_METRICS = [

  {

    key: "retrieval_relevance",

    label: "Retrieval relevance",

  },

  {

    key: "faithfulness",

    label: "Faithfulness",

  },

  {

    key: "answer_relevance",

    label: "Answer relevance",

  },

  {

    key: "safety_compliance",

    label: "Safety compliance",

  },

];



function formatTime(date = new Date()) {

  return date.toLocaleTimeString([], {

    hour: "2-digit",

    minute: "2-digit",

  });

}



function createMessage(role, content, extra = {}) {

  return {

    id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,

    role,

    content,

    time: formatTime(),

    ...extra,

  };

}



function formatScore(value) {

  return typeof value === "number" && Number.isFinite(value)

    ? value.toFixed(1)

    : "—";

}



function getErrorMessage(error) {

  if (error instanceof TypeError) {

    return (

      "Unable to connect to the backend. Check that FastAPI is running " +

      "and that the API URL is correct."

    );

  }



  return error.message || "Something went wrong. Please try again.";

}



/* -------------------- Answer evaluation -------------------- */



function EvaluationCard({ evaluation }) {

  if (!evaluation || typeof evaluation !== "object") {

    return null;

  }



  const decision = String(evaluation.decision || "UNKNOWN").toUpperCase();



  const score =

    typeof evaluation.overall_score === "number"

      ? Math.min(10, Math.max(0, evaluation.overall_score))

      : null;



  return (

    <section className="dl-evaluation-card">

      <div className="dl-evaluation-heading">

        <div>

          <span className="dl-section-eyebrow">QUALITY REPORT</span>

          <h4>Answer evaluation</h4>

        </div>



        <span

          className={`dl-decision dl-decision-${decision

            .toLowerCase()

            .replace(/_/g, "-")}`}

        >

          {decision.replace(/_/g, " ")}

        </span>

      </div>



      <div className="dl-overall-score">

        <div>

          <span>Overall score</span>

          <strong>

            {formatScore(score)}

            <small> / 10</small>

          </strong>

        </div>



        <div

          className="dl-score-track"

          role="progressbar"

          aria-label="Overall evaluation score"

          aria-valuemin={0}

          aria-valuemax={10}

          aria-valuenow={score ?? 0}

        >

          <span

            style={{

              width: `${score === null ? 0 : score * 10}%`,

            }}

          />

        </div>

      </div>



      <div className="dl-evaluation-grid">

        {EVALUATION_METRICS.map((metric) => (

          <div className="dl-evaluation-metric" key={metric.key}>

            <span>{metric.label}</span>

            <strong>{formatScore(evaluation[metric.key])}</strong>

            <small>/ 10</small>

          </div>

        ))}

      </div>



      {evaluation.reason && (

        <p className="dl-evaluation-reason">{evaluation.reason}</p>

      )}



      {evaluation.evaluation_id != null && (

        <p className="dl-evaluation-id">

          Evaluation ID: {evaluation.evaluation_id}

        </p>

      )}

    </section>

  );

}



/* -------------------- Retrieved document sources -------------------- */



function SourceList({ sources }) {

  const [expanded, setExpanded] = useState(false);



  if (!Array.isArray(sources) || sources.length === 0) {

    return null;

  }



  return (

    <section className="dl-sources">

      <button

        type="button"

        className="dl-sources-toggle"

        onClick={() => setExpanded((current) => !current)}

        aria-expanded={expanded}

      >

        <span className="dl-source-icon" aria-hidden="true">

          ▤

        </span>



        <span>

          <strong>

            {sources.length} source{sources.length === 1 ? "" : "s"} retrieved

          </strong>

          <small>Explore the documents used for this answer</small>

        </span>



        <span className="dl-expand-icon" aria-hidden="true">

          {expanded ? "−" : "+"}

        </span>

      </button>



      {expanded && (

        <div className="dl-source-list">

          {sources.map((source, index) => (

            <article

              className="dl-source-item"

              key={`${source.chunk_id ?? index}-${source.file_name ?? "document"}`}

            >

              <div className="dl-source-file-icon">DOC</div>



              <div className="dl-source-details">

                <strong>{source.file_name || "Uploaded document"}</strong>



                <span>

                  Chunk {source.chunk_index ?? "—"}

                  {source.document_id != null

                    ? ` · Document ${source.document_id}`

                    : ""}

                </span>

              </div>



              {typeof source.similarity === "number" && (

                <span className="dl-source-score">

                  {(source.similarity * 100).toFixed(1)}%

                  <small> similarity</small>

                </span>

              )}

            </article>

          ))}

        </div>

      )}

    </section>

  );

}



/* -------------------- Browser voice output -------------------- */

function speakText(text) {
  if (!("speechSynthesis" in window)) {
    window.alert("Text-to-speech is not supported in this browser.");
    return;
  }
  window.speechSynthesis.cancel();
  const plainText = String(text || "").replace(/[#*_`>\[\]()]/g, " ").replace(/\s+/g, " ").trim();
  if (!plainText) return;
  const utterance = new SpeechSynthesisUtterance(plainText);
  utterance.lang = "en-IN";
  utterance.rate = 1;
  window.speechSynthesis.speak(utterance);
}

/* -------------------- Individual chat messages -------------------- */



function ChatMessage({ message }) {

  const isUser = message.role === "user";



  const hasEvaluation =

    !isUser &&

    message.id !== "welcome" &&

    message.evaluation != null;



  return (

    <article

      className={`dl-message ${

        isUser ? "dl-message-user" : "dl-message-assistant"

      }`}

    >

      <div className="dl-message-avatar" aria-hidden="true">

        {isUser ? "U" : "D"}

      </div>



      <div className="dl-message-body">

        <div className="dl-message-meta">

          <strong>{isUser ? "You" : "DocuLens AI"}</strong>

          {message.time && <time>{message.time}</time>}

        </div>



        <div className="dl-message-bubble">

        <ReactMarkdown remarkPlugins={[remarkGfm]}>

            {message.content}

        </ReactMarkdown>

        </div>

        {!isUser && message.id !== "welcome" && (
          <div className="dl-voice-message-actions">
            <button type="button" className="dl-voice-icon-button" onClick={() => speakText(message.content)} aria-label="Read answer aloud" title="Read answer aloud">
              🔊 <span>Listen</span>
            </button>
          </div>
        )}

        {!isUser && (

          <>

            <SourceList sources={message.sources} />



            {message.relevance?.reason && (

              <div

                className={`dl-relevance-note ${

                  message.relevance.relevant

                    ? "dl-relevance-positive"

                    : "dl-relevance-neutral"

                }`}

              >

                <span aria-hidden="true">

                  {message.relevance.relevant ? "✓" : "ⓘ"}

                </span>

                <span>{message.relevance.reason}</span>

              </div>

            )}



            {hasEvaluation && (

              <EvaluationCard evaluation={message.evaluation} />

            )}

          </>

        )}

      </div>

    </article>

  );

}



/* -------------------- Information cards -------------------- */



function WorkspaceCard() {

  return (

    <section className="dl-side-card dl-capability-card">

      <div className="dl-side-card-icon" aria-hidden="true">

        ✦

      </div>



      <span className="dl-section-eyebrow">YOUR AI WORKSPACE</span>



      <h3>Answers grounded in your documents</h3>



      <p>

        DocuLens retrieves relevant document passages to help you explore

        information and understand where an answer came from.

      </p>



      <div className="dl-capability-list">

        <div>

          <span>✓</span> Semantic document retrieval

        </div>

        <div>

          <span>✓</span> Source-level transparency

        </div>

        <div>

          <span>✓</span> Answer quality evaluation when available

        </div>

      </div>

    </section>

  );

}



function ConversationCard({ requestCount, isSending }) {

  return (

    <section className="dl-side-card">

      <div className="dl-side-card-heading">

        <h3>Conversation overview</h3>

        <span className="dl-count-pill">{requestCount}</span>

      </div>



      <div className="dl-session-stat">

        <span>Questions sent</span>

        <strong>{requestCount}</strong>

      </div>



      <div className="dl-session-stat">

        <span>Current status</span>

        <strong className="dl-session-ready">

          {isSending ? "Processing" : "Ready"}

        </strong>

      </div>



      <p className="dl-sidebar-note">

        Start a new conversation whenever you want to explore a different

        topic.

      </p>

    </section>

  );

}



function QuestionTipsCard() {

  return (

    <section className="dl-side-card dl-note-card">

      <div className="dl-side-card-icon" aria-hidden="true">

        ?

      </div>



      <span className="dl-section-eyebrow">MAKE THE MOST OF DOCULENS</span>



      <h3>Ask naturally</h3>



      <p>

        Ask a direct question, request a summary, or explore a specific

        topic. Minor spelling mistakes are okay, but clearer questions

        can help retrieval find the most relevant passages.

      </p>

    </section>

  );

}



/* -------------------- Main chatbot page -------------------- */



function ChatPage() {

  const [messages, setMessages] = useState([WELCOME_MESSAGE]);

  const [question, setQuestion] = useState("");

  const [conversationId, setConversationId] = useState(null);

  const [isSending, setIsSending] = useState(false);

  const [error, setError] = useState("");

  const [requestCount, setRequestCount] = useState(0);
  const [isListening, setIsListening] = useState(false);
  const [voiceError, setVoiceError] = useState("");
  const recognitionRef = useRef(null);

  const textareaRef = useRef(null);

  const messagesEndRef = useRef(null);



  useEffect(() => {

    messagesEndRef.current?.scrollIntoView({

      behavior: "smooth",

      block: "end",

    });

  }, [messages, isSending]);



  function startNewChat() {

    if (isSending) return;



    setMessages([

      {

        ...WELCOME_MESSAGE,

        time: formatTime(),

      },

    ]);



    setQuestion("");

    setConversationId(null);

    setError("");

    setRequestCount(0);



    textareaRef.current?.focus();

  }



  async function sendMessage(event) {

    event?.preventDefault();



    const cleanQuestion = question.trim();



    if (!cleanQuestion || isSending) {

      return;

    }



    if (cleanQuestion.length > MAX_QUESTION_LENGTH) {

      setError(

        `Your question must contain no more than ${MAX_QUESTION_LENGTH.toLocaleString()} characters.`

      );

      return;

    }



    setError("");

    setQuestion("");

    setIsSending(true);



    setMessages((current) => [

      ...current,

      createMessage("user", cleanQuestion),

    ]);



    const requestConversationId = conversationId;



    try {

      const controller = new AbortController();

      const timeoutId = window.setTimeout(() => controller.abort(), 120000);



      let response;



      try {

        response = await fetch(`${API_BASE_URL}/chat/`, {

          method: "POST",

          headers: {

            "Content-Type": "application/json",

            Accept: "application/json",

          },

          body: JSON.stringify({

            question: cleanQuestion,

            conversation_id: requestConversationId,

            top_k: 5,

          }),

          signal: controller.signal,

        });

      } finally {

       window.clearTimeout(timeoutId);

      }



      let data;



      try {

        data = await response.json();

      } catch {

        throw new Error(

          `The backend returned an invalid response (HTTP ${response.status}).`

        );

      }



      if (!response.ok) {

        const detail =

          typeof data.detail === "string"

            ? data.detail

            : `The request failed with HTTP ${response.status}.`;



        throw new Error(detail);

      }



      if (typeof data.answer !== "string") {

        throw new Error("The backend response did not contain an answer.");

      }



      if (data.conversation_id) {

        setConversationId(data.conversation_id);

      }



      const assistantMessage = createMessage("assistant", data.answer, {

        sources: Array.isArray(data.sources) ? data.sources : [],

        evaluation: data.evaluation ?? null,

        relevance: data.relevance ?? null,

      });



      setMessages((current) => [...current, assistantMessage]);

      setRequestCount((current) => current + 1);

    } catch (requestError) {

      const message =

        requestError.name === "AbortError"

          ? "The request took too long. Please try again."

          : getErrorMessage(requestError);



      setError(message);

    } finally {

      setIsSending(false);

      textareaRef.current?.focus();

    }

  }



  function toggleVoiceInput() {
    setVoiceError("");
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceError("Voice input is not supported in this browser. Try Chrome or type your question.");
      return;
    }
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }
    window.speechSynthesis?.cancel();
    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.continuous = false;
    recognition.interimResults = true;
    recognitionRef.current = recognition;
    recognition.onstart = () => setIsListening(true);
    recognition.onresult = (event) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        transcript += event.results[i][0].transcript;
      }
      setQuestion(transcript.trim());
    };
    recognition.onerror = (event) => {
      setVoiceError(event.error === "not-allowed" ? "Microphone permission was denied. Allow microphone access in your browser." : `Voice input failed: ${event.error}. You can type your question instead.`);
      setIsListening(false);
    };
    recognition.onend = () => setIsListening(false);
    try { recognition.start(); } catch {
      setVoiceError("Could not start the microphone. Please try again.");
      setIsListening(false);
    }
  }

  useEffect(() => () => {
    recognitionRef.current?.stop();
    window.speechSynthesis?.cancel();
  }, []);

  function handleKeyDown(event) {

    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {

      event.preventDefault();

      sendMessage();

    }

  }



  return (

    <section className="page dl-chat-page">

      {/* Page heading */}

      <div className="page-heading dl-chat-page-heading">

        <div>

          <span className="eyebrow">RETRIEVAL & EVALUATION</span>



          <h2>Retrieval + Chatbot</h2>



          <p className="dl-chat-intro">

            <strong>Your documents. Your insights. One intelligent assistant.</strong>

            <span>

                Ask questions, discover key information, and explore your uploaded

                documents through clear, source-grounded answers.

            </span>

            </p>

        </div>



        <button

          type="button"

          className="secondary-button dl-new-chat-button"

          onClick={startNewChat}

          disabled={isSending}

        >

          <span aria-hidden="true">＋</span> New conversation

        </button>

      </div>



      {/* Main conversation */}

      <div className="dl-chat-layout">

        <section className="dl-chat-panel">

          <header className="dl-chat-toolbar">

            <div className="dl-assistant-identity">

              <div className="dl-assistant-logo">D</div>



              <div>

                <strong>DocuLens AI</strong>



                <span>

                  <i aria-hidden="true" />

                  Document-grounded assistant

                </span>

              </div>

            </div>



            <div className="dl-session-info" aria-live="polite">

              <span

                className="dl-session-indicator"

                aria-hidden="true"

                style={

                  isSending

                    ? { background: "#d99a27" }

                    : undefined

                }

              />

              {isSending ? "Working..." : "Ready to help"}

            </div>

          </header>



          <div

            className="dl-messages"

            role="log"

            aria-label="Chat messages"

            aria-live="polite"

            aria-relevant="additions"

          >

            {messages.map((message) => (

              <ChatMessage key={message.id} message={message} />

            ))}



            {isSending && (

              <div className="dl-message dl-message-assistant">

                <div className="dl-message-avatar" aria-hidden="true">

                  D

                </div>



                <div className="dl-message-body">

                  <div className="dl-message-meta">

                    <strong>DocuLens AI</strong>

                    <span>Preparing your response</span>

                  </div>



                  <div

                    className="dl-typing-indicator"

                    role="status"

                    aria-label="DocuLens is preparing a response"

                  >

                    <span />

                    <span />

                    <span />

                  </div>



                  <p className="dl-thinking-label">

                    Finding relevant information and preparing an answer...

                  </p>

                </div>

              </div>

            )}



            <div ref={messagesEndRef} />

          </div>



          {error && (

            <div className="dl-chat-error" role="alert">

              <span aria-hidden="true">!</span>



              <div>

                <strong>Unable to complete the request</strong>

                <p>{error}</p>

              </div>



              <button

                type="button"

                onClick={() => setError("")}

                aria-label="Dismiss error"

              >

                ×

              </button>

            </div>

          )}



          {voiceError && <p className="dl-voice-error" role="status">{voiceError}</p>}

          {/* Message composer */}

          <form className="dl-composer" onSubmit={sendMessage}>

            <label className="dl-composer-label" htmlFor="dl-chat-question">

              Your question

            </label>



            <div className="dl-composer-input-wrap">

              <textarea

                ref={textareaRef}

                id="dl-chat-question"

                value={question}

                onChange={(event) => setQuestion(event.target.value)}

                onKeyDown={handleKeyDown}

                placeholder="Ask a question, request a summary, or explore your documents..."

                rows={2}

                maxLength={MAX_QUESTION_LENGTH}

                disabled={isSending}

                aria-describedby="dl-composer-hint"

              />



              <button
                type="button"
                className={`dl-voice-button ${isListening ? "is-listening" : ""}`}
                onClick={toggleVoiceInput}
                disabled={isSending}
                aria-label={isListening ? "Stop voice input" : "Start voice input"}
                title={isListening ? "Stop listening" : "Ask by voice"}
              >
                {isListening ? "■" : "🎙"}
              </button>

              <button

                type="submit"

                className="dl-send-button"

                disabled={!question.trim() || isSending}

                aria-label="Send message"

              >

                {isSending ? "…" : "↑"}

              </button>

            </div>



            <div className="dl-composer-footer">

              <span id="dl-composer-hint">
                {isListening ? "Listening… speak your question" : "Enter to send · Shift + Enter for a new line"}
              </span>



              <span>

                {question.length.toLocaleString()} /{" "}

                {MAX_QUESTION_LENGTH.toLocaleString()}

              </span>

            </div>

          </form>

        </section>

      </div>



      {/* Information cards now appear below the chat */}

      <aside className="dl-chat-sidebar" aria-label="Chat information">

        <WorkspaceCard />



        <ConversationCard

          requestCount={requestCount}

          isSending={isSending}

        />



        <QuestionTipsCard />

      </aside>



      <p className="dl-chat-disclaimer">

        AI-generated answers can be incomplete or incorrect. Review available

        sources and evaluation results before relying on an answer.

      </p>

    </section>

  );

}



export default ChatPage;