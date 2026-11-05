import { BrowserRouter, Routes, Route } from "react-router-dom";

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
function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Navbar />

        <main className="app-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/oauth/callback" element={<OAuthCallback />} />
            <Route path="/register" element={<Register />} />
            <Route path="/profile" element={<UserProfile />} />
            <Route path="/interview-setup" element={<InterviewSetup />} />
            <Route path="/interview" element={<Interview />} />
            <Route path="/test" element={<Test />} />
            <Route path="/results" element={<Results />} />
            <Route path="/ask-question" element={<AskQuestion />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
