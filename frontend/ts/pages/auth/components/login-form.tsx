// src/Pages/Auth/components/login-form.tsx
import { useRef, useState } from "react";
import { Link } from "@inertiajs/react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";

import { Button } from "@/components/ui/button";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldSeparator,
  FieldSet,
} from "@/components/ui/field";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
} from "@/components/ui/input-group";
import { toast } from "sonner";
import { EyeClosed, Eye, LockIcon, MailIcon } from "lucide-react";
import { apiClient, type ApiErrorResponse } from "@/lib/axios";
import { useAuthStore } from "@/stores/authStore";
import { Spinner } from "@/components/ui/spinner";
import { router } from "@inertiajs/react";
import Axios from "axios";

gsap.registerPlugin(useGSAP); // Register the hook

const LoginForm = () => {
  const formRef = useRef<HTMLFormElement>(null);
  const [isPasswordVisible, setPasswordVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setError] = useState<string | null>(null);
  const setTokens = useAuthStore((state) => state.setTokens);
  const setUser = useAuthStore((state) => state.setUser);

  useGSAP(
    () => {
      gsap.from(formRef.current, {
        opacity: 0,
        y: 20,
        duration: 0.8,
        ease: "power3.out",
      });
    },
    { scope: formRef } // Scope pour cibler les sélecteurs à l'intérieur du container
  );

  const handleSubmint = (e: React.FormEvent) => {
    e.preventDefault();
    const login = async () => {
      const formData = new FormData(formRef.current!);
      const email = formData.get("email") as string;
      const password = formData.get("password") as string;

      try {
        setIsLoading(true);
        const { data } = await apiClient.post("auth/login", { email, password });

        setTokens(data.access_token, data.refresh_token);
        setError(null);
        toast.success("Connexion reussie.");
        formRef.current?.reset();
        const response = await apiClient.get("auth/me");
        setUser(response.data);
        router.visit("/feeds");
      } catch (error) {
        if (Axios.isAxiosError<ApiErrorResponse>(error)) {
          const message =
            error.response?.data?.detail || "Erreur lors de la connexion.";
          setError(message);
          toast.error(message);
        } else {
          setError("Erreur lors de la connexion.");
          toast.error("Erreur lors de la connexion.");
        }
      } finally {
        setIsLoading(false);
      }
    };
    login();
  };

  return (
    <form ref={formRef} className="w-full" onSubmit={handleSubmint}>
      <FieldGroup className="border-none">
        <div className="flex flex-col items-center gap-1 text-center">
          <h1 className="text-2xl font-bold">Se connecter</h1>
          <p className="text-muted-foreground text-sm text-balance">
            Entrez vos identifiants pour acceder a votre compte.
          </p>
        </div>
        {errorMessage && (
          <div className="my-4 rounded-md bg-red-100 p-4">
            <p className="text-sm text-red-700">{errorMessage}</p>
          </div>
        )}
        {/* Email Field */}
        <Field>
          <FieldLabel htmlFor="email">Email</FieldLabel>
          <InputGroup>
            <InputGroupInput
              type="email"
              name="email"
              placeholder="Entrez votre email"
            />
            <InputGroupAddon>
              <MailIcon />
            </InputGroupAddon>
          </InputGroup>
        </Field>
        {/* Password Field */}
        <Field>
          <div className="flex items-center">
            <FieldLabel htmlFor="password">Mot de passe</FieldLabel>
            <Link
              href="/password-reset"
              className="ml-auto text-sm underline-offset-4 hover:underline"
            >
              Mot de passe oublie ?
            </Link>
          </div>

          <InputGroup>
            <InputGroupInput
              placeholder="Entrez votre mot de passe"
              name="password"
              type={isPasswordVisible ? "text" : "password"}
            />
            <InputGroupAddon>
              <LockIcon />
            </InputGroupAddon>
            <InputGroupAddon
              align="inline-end"
              className="cursor-pointer"
              onClick={() => setPasswordVisible(!isPasswordVisible)}
            >
              {isPasswordVisible ? <Eye /> : <EyeClosed />}
            </InputGroupAddon>
          </InputGroup>
        </Field>

        <FieldSet>
          <Field>
            <Button
              type="submit"
              className="w-full"
              size={"icon"}
              disabled={isLoading}
            >
              {isLoading ? <Spinner /> : "Se connecter"}
            </Button>
          </Field>
        </FieldSet>
        {/* Sign In Button */}

        <FieldSeparator>Ou</FieldSeparator>

        <Field>
          <FieldDescription className="text-center text-sm text-muted-foreground">
            Nouveau ENSPM Hub?{" "}
            <Link href="#" className="font-bold text-primary hover:underline">
              S'inscrire
            </Link>
          </FieldDescription>
        </Field>
      </FieldGroup>
    </form>
  );
};

export default LoginForm;
