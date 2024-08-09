"use client";
import { Button } from "../components/ui/button";
import { Provider } from "@supabase/supabase-js";
import { Github } from "lucide-react"; 
import { oAuthSignIn } from "./actions";

export function OAuthButtons() {
  // You can remove the OAuthProvider type as you only have one provider for now.
  return (
    <Button
      className="w-full flex items-center justify-center gap-2"
      variant="outline"
      onClick={async () => {
        await oAuthSignIn('github'); 
      }}
    >
      <Github className="size-5" />
      <span>Login with GitHub</span>
    </Button>
  );
}