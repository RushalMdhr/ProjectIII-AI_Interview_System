import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";

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
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppChrome />
    </BrowserRouter>
  );
}

export default App;
