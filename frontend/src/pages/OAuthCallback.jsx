import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";

function OAuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    const callbackParams = new URLSearchParams(window.location.hash.slice(1));
    const accessToken = callbackParams.get("access");
    const refreshToken = callbackParams.get("refresh");
    const user = callbackParams.get("user");

    if (!accessToken || !refreshToken || !user) {
      const msg = "Google sign-in was interrupted. Please try again.";
      toast.error(msg);
      navigate("/login", { replace: true });
      return;
    }

    try {
      localStorage.setItem("accessToken", accessToken);
      localStorage.setItem("refreshToken", refreshToken);
      localStorage.setItem("currentUser", user);

      const parsedUser = JSON.parse(user);
      const displayName = parsedUser?.first_name || parsedUser?.name || "there";
      toast.success(`Welcome back, ${displayName}!`);
      navigate("/", { replace: true });
    } catch {
      const msg = "Google sign-in failed. Please try again.";
      toast.error(msg);
      navigate("/login", { replace: true });
    }
  }, [navigate]);

  return null;
}

export default OAuthCallback;
