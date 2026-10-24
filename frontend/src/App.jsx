import {
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";

import IngestionPage from "./pages/IngestionPage";
import GuardrailsPage from "./pages/GuardrailsPage";
import ChatPage from "./pages/ChatPage";

const navigationItems = [
  {
    path: "/ingestion",
    label: "Data Ingestion",
    icon: "▤",
    description: "Upload and prepare documents",
  },
  {
    path: "/guardrails",
    label: "Guardrails",
    icon: "◇",
    description: "Manage safety controls",
  },
  {
    path: "/chat",
    label: "Retrieval + Chatbot",
    icon: "◉",
    description: "Ask questions and evaluate answers",
  },
];

function App() {
  const location = useLocation();

  const currentPage =
    navigationItems.find((item) => item.path === location.pathname) ??
    navigationItems[0];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark">D</div>

          <div className="brand-copy">
            <h1>DocuLens</h1>
            <span>RAG Evaluation Platform</span>
          </div>
        </div>

        <div className="sidebar-section-label">WORKSPACE</div>

        <nav className="sidebar-navigation" aria-label="Main navigation">
          {navigationItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `sidebar-link${isActive ? " active" : ""}`
              }
            >
              <span className="sidebar-link-icon" aria-hidden="true">
                {item.icon}
              </span>

              <span className="sidebar-link-copy">
                <span className="sidebar-link-label">{item.label}</span>
                <span className="sidebar-link-description">
                  {item.description}
                </span>
              </span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-status-dot" />

          <div>
            <strong>Local evaluation</strong>
            <span>Laya model configured</span>
          </div>
        </div>
      </aside>

      <div className="workspace">
        <header className="top-header">
          <div className="breadcrumb">
            <span>Workspace</span>
            <span className="breadcrumb-separator">/</span>
            <strong>{currentPage.label}</strong>
          </div>

          <div className="header-right">
            <div className="connection-status">
              <span className="connection-dot" />
              Backend workspace
            </div>

            <div className="user-avatar" title="DocuLens user">
              D
            </div>
          </div>
        </header>

        <main className="main-content">
          <Routes>
            <Route
              path="/"
              element={<Navigate to="/ingestion" replace />}
            />

            <Route
              path="/ingestion"
              element={<IngestionPage />}
            />

            <Route
              path="/guardrails"
              element={<GuardrailsPage />}
            />

            <Route
              path="/chat"
              element={<ChatPage />}
            />

            <Route
              path="*"
              element={<Navigate to="/ingestion" replace />}
            />
          </Routes>
        </main>

        <footer className="workspace-footer">
          <span>DocuLens</span>
          <span>Document-grounded AI · RAG evaluation</span>
        </footer>
      </div>
    </div>
  );
}

export default App;