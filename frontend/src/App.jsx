import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';


import Navbar from "./components/Navbar";
// import Footer from "./components/Footer";
import Home from "./pages/home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import InterviewSetup from "./pages/InterviewSetup";
import Interview from "./pages/Interview";
import Results from "./pages/Results";
import Test from "./pages/test";
import AskQuestion from "./pages/AskQuestion";
import UserProfile from "./pages/UserProfile";
import OAuthCallback from "./pages/OAuthCallback";
import ResetPassword from "./pages/ResetPassword";
import AdminDashboard from "./pages/AdminDashboard";
import NotFound from "./pages/NotFound";

function ProtectedRoute({ children }) {
  const location = useLocation();

  if (!localStorage.getItem("accessToken")) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

function AppChrome() {
  const location = useLocation();
  const isAdminRoute = location.pathname.startsWith("/admin");
  const shellClass = isAdminRoute ? "" : "app-layout";
  let isSuperuser = false;
  try {
    isSuperuser = JSON.parse(localStorage.getItem("currentUser") || "null")?.is_superuser === true;
  } catch {
    isSuperuser = false;
  }

  if (isSuperuser && !isAdminRoute) {
    return <Navigate to="/admin/dashboard" replace />;
  }

  return (
    <div className={shellClass}>
      {!isAdminRoute && <Navbar />}
      <main className={isAdminRoute ? "" : "app-content"}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/oauth/callback" element={<OAuthCallback />} />
          <Route
            path="/reset-password/:uid/:token"
            element={<ResetPassword />}
          />
          <Route path="/register" element={<Register />} />
          <Route path="/profile" element={<UserProfile />} />
          <Route
            path="/interview-setup"
            element={
              <ProtectedRoute>
                <InterviewSetup />
              </ProtectedRoute>
            }
          />
          <Route
            path="/interview"
            element={
              <ProtectedRoute>
                <Interview />
              </ProtectedRoute>
            }
          />
          <Route path="/test" element={<Test />} />
          <Route
            path="/admin"
            element={<Navigate to="/admin/dashboard" replace />}
          />
          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/results"
            element={
              <ProtectedRoute>
                <Results />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ask-question"
            element={
              <ProtectedRoute>
                <AskQuestion />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  );
}


function App() {
  return (
    <>
      <style>{`
        .Toastify__toast-container {
          top: 18px;
          right: 18px;
        }

        .Toastify__toast {
          border-radius: 16px !important;
          border: 1px solid rgba(255,255,255,0.12) !important;
          box-shadow: 0 20px 40px -18px rgba(6,10,26,0.8) !important;
          font-family: Inter, Arial, sans-serif !important;
          backdrop-filter: blur(14px);
          -webkit-backdrop-filter: blur(14px);
          padding: 12px 14px !important;
        }

        .Toastify__toast-body {
          color: #FBFAFF !important;
          font-size: 14px !important;
          font-weight: 600 !important;
          padding: 0 !important;
          line-height: 1.4 !important;
        }

        .Toastify__toast-icon {
          width: 20px !important;
          margin-inline-end: 10px !important;
        }

        .Toastify__close-button {
          color: rgba(251,250,255,0.8) !important;
          opacity: 1 !important;
        }

        .Toastify__close-button:hover {
          color: #FBFAFF !important;
        }

        .Toastify__progress-bar {
          height: 4px !important;
          border-radius: 999px !important;
        }

        .Toastify__toast--success {
          background: rgba(20, 31, 41, 0.88) !important;
          border-left: 4px solid #45E0D0 !important;
        }

        .Toastify__toast--error {
          background: rgba(35, 19, 22, 0.9) !important;
          border-left: 4px solid #FF7A7A !important;
        }

        .Toastify__toast--info {
          background: rgba(28, 31, 58, 0.9) !important;
          border-left: 4px solid #8B7CF6 !important;
        }

        .Toastify__progress-bar--success {
          background: linear-gradient(90deg, #45E0D0, #FFB35B) !important;
        }

        .Toastify__progress-bar--error {
          background: linear-gradient(90deg, #FF7A7A, #FFB35B) !important;
        }

        .Toastify__progress-bar--info {
          background: linear-gradient(90deg, #8B7CF6, #45E0D0) !important;
        }
      `}</style>

      <BrowserRouter>
        <AppChrome />
      </BrowserRouter>

      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        pauseOnHover
        theme="dark"
      />
    </>
  );
}

export default App;

