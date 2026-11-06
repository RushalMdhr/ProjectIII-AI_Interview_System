import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

function OAuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    const callbackParams = new URLSearchParams(window.location.hash.slice(1));
    const accessToken = callbackParams.get("access");
    const refreshToken = callbackParams.get("refresh");
    const user = callbackParams.get("user");

    if (!accessToken || !refreshToken || !user) {
      navigate("/", { replace: true });
      return;
    }

    try {
      localStorage.setItem("accessToken", accessToken);
      localStorage.setItem("refreshToken", refreshToken);
      localStorage.setItem("currentUser", user);
      navigate("/", { replace: true });
    } catch {
      navigate("/login", { replace: true });
    }
  }, [navigate]);

  return null;
}

export default OAuthCallback;
