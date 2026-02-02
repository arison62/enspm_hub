import { useState, useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Loader2,
  Mail,
  MessageSquare,
  Timer,
  ArrowRight,
  ArrowLeft,
} from "lucide-react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";

// UI Components (Shadcn)
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
} from "@/components/ui/input-otp";
import { toast } from "sonner";
import axios from "@/lib/axios";
import { router } from "@inertiajs/react";

// --- VALIDATION SCHEMAS ---
const requestSchema = z.object({
  identifier: z.string().min(3, "L'identifiant est requis"),
});

const resetSchema = z
  .object({
    otp: z.string().length(6, "Le code doit contenir exactement 6 chiffres"),
    password: z
      .string()
      .min(8, "Minimum 8 caractères requis")
      .regex(/[A-Z]/, "Au moins une lettre majuscule requise")
      .regex(/[a-z]/, "Au moins une lettre minuscule requise")
      .regex(/[0-9]/, "Au moins un chiffre requis"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Les mots de passe ne correspondent pas",
    path: ["confirmPassword"],
  });

export default function PasswordResetForm() {
  // --- ÉTATS ---
  const [step, setStep] = useState<"request" | "verify">("request");
  const [method, setMethod] = useState<"email" | "sms">("email");
  const [cooldown, setCooldown] = useState(0);
  const [targetIdentifier, setTargetIdentifier] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLDivElement>(null);

  // --- PERSISTANCE & TIMER ---
  useEffect(() => {
    // Vérification du LocalStorage au montage
    const checkCooldown = () => {
      const storedTarget = localStorage.getItem("reset_otp_cooldown_target");
      if (storedTarget) {
        const targetTime = parseInt(storedTarget, 10);
        const now = Date.now();
        const remaining = Math.ceil((targetTime - now) / 1000);

        if (remaining > 0) {
          setCooldown(remaining);
        } else {
          localStorage.removeItem("reset_otp_cooldown_target");
        }
      }
    };
    checkCooldown();

    const interval = setInterval(() => {
      setCooldown((prev) => {
        if (prev <= 1) {
          if (prev === 1) localStorage.removeItem("reset_otp_cooldown_target");
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // --- ANIMATIONS GSAP ---
  useGSAP(
    () => {
      gsap.fromTo(
        containerRef.current,
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" },
      );
    },
    { scope: containerRef },
  );

  // Animation lors du changement d'étape
  useGSAP(() => {
    gsap.fromTo(
      formRef.current,
      { opacity: 0, x: step === "verify" ? 20 : -20 },
      { opacity: 1, x: 0, duration: 0.4, ease: "power2.out" },
    );
  }, [step]);

  // --- LOGIQUE MÉTIER ---

  const startCooldown = () => {
    const durationSeconds = 180; // 3 minutes
    const targetTime = Date.now() + durationSeconds * 1000;
    localStorage.setItem("reset_otp_cooldown_target", targetTime.toString());
    setCooldown(durationSeconds);
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  // Forms Hooks
  const requestForm = useForm<z.infer<typeof requestSchema>>({
    resolver: zodResolver(requestSchema),
    defaultValues: { identifier: "" },
  });

  const resetForm = useForm<z.infer<typeof resetSchema>>({
    resolver: zodResolver(resetSchema),
    defaultValues: { otp: "", password: "", confirmPassword: "" },
  });

  // Handlers
  const onRequestSubmit = async (values: z.infer<typeof requestSchema>) => {
    setIsLoading(true);
    try {
      const response = await axios.post("auth/password-reset-request", {
        method,
        user_id: values.identifier,
      });
      if (response.status !== 204) {
        const errorMsg =
          response.data?.detail || "Erreur lors de l'envoi du code.";
        toast.error(errorMsg);
        return;
      }
      setTargetIdentifier(values.identifier);
      startCooldown();

      // Animation de sortie avant changement de state
      if (formRef.current) {
        await gsap.to(formRef.current, { opacity: 0, x: -20, duration: 0.2 });
      }
      setStep("verify");
      toast.success("Code envoyé.");
    } catch (error) {
      console.error(error);
      toast.error("Impossible d'envoyer le code.");
    } finally {
      setIsLoading(false);
    }
  };

  const onResetSubmit = async (values: z.infer<typeof resetSchema>) => {
    setIsLoading(true);
    try {
      const response = await axios.post("auth/password-reset-confirm", {
        token: values.otp,
        new_password: values.password,
        user_id: targetIdentifier,
      });
      if (response.status !== 204) {
        const errorMsg =
          response.data?.detail ||
          "Erreur lors de la mise à jour du mot de passe.";
        toast.error(errorMsg);
        return;
      }

      toast.success("Mot de passe réinitialisé avec succès.");

      // Redirection
      router.visit("/login");
    } catch (error) {
      console.error(error);
      toast.error("Code invalide.");
    } finally {
      setIsLoading(false);
    }
  };

  // --- RENDER ---
  return (
    <div ref={containerRef} className="w-full max-w-md mx-auto">
      {/* HEADER DE NAVIGATION (Optionnel, pour UX) */}
      <div className="mb-6 flex justify-center">
        <div className="flex items-center gap-2 text-sm">
          <span
            className={`px-3 py-1 rounded-full ${
              step === "request"
                ? "bg-primary text-white"
                : "bg-gray-200 text-gray-500"
            }`}
          >
            1. Demande
          </span>
          <div className="w-8 h-[2px] bg-gray-200"></div>
          <span
            className={`px-3 py-1 rounded-full ${
              step === "verify"
                ? "bg-primary text-white"
                : "bg-gray-200 text-gray-500"
            }`}
          >
            2. Validation
          </span>
        </div>
      </div>

      <div ref={formRef}>
        {step === "request" ? (
          /* --- ÉTAPE 1 : DEMANDE --- */
          <div className="space-y-6">
            <Tabs
              value={method}
              onValueChange={(v) => setMethod(v as "email" | "sms")}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-2 mb-4">
                <TabsTrigger value="email" className="flex items-center gap-2">
                  <Mail className="h-4 w-4" /> Email
                </TabsTrigger>
                <TabsTrigger
                  value="sms"
                  disabled
                  className="flex items-center gap-2 opacity-50 cursor-not-allowed"
                >
                  <MessageSquare className="h-4 w-4" /> SMS
                </TabsTrigger>
              </TabsList>

              <Form {...requestForm}>
                <form
                  onSubmit={requestForm.handleSubmit(onRequestSubmit)}
                  className="space-y-4"
                >
                  <FormField
                    control={requestForm.control}
                    name="identifier"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          {method === "email"
                            ? "Adresse Email"
                            : "Numéro de téléphone"}
                        </FormLabel>
                        <FormControl>
                          <Input
                            placeholder={
                              method === "email"
                                ? "ex: 1d5dA@example.com"
                                : "+237 XXXXXXXX"
                            }
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {cooldown > 0 ? (
                    <Button
                      type="button"
                      disabled
                      className="w-full h-11"
                      variant="outline"
                    >
                      <Timer className="mr-2 h-4 w-4 animate-pulse text-orange-500" />
                      Veuillez patienter {formatTime(cooldown)}
                    </Button>
                  ) : (
                    <Button
                      type="submit"
                      className="w-full group"
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        "Recevoir le code"
                      )}
                      {!isLoading && (
                        <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                      )}
                    </Button>
                  )}
                </form>
              </Form>
            </Tabs>

            {/* Lien raccourci si déjà reçu */}
            <div className="text-center">
              <button
                onClick={() => setStep("verify")}
                className="text-sm text-gray-500 hover:text-primary underline decoration-dotted underline-offset-4"
              >
                J'ai déjà un code de validation
              </button>
            </div>
          </div>
        ) : (
          /* --- ÉTAPE 2 : VALIDATION --- */
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h3 className="font-medium text-lg">Vérification de sécurité</h3>
              <p className="text-sm text-gray-500">
                Entrez le code envoyé à{" "}
                <span className="font-semibold text-gray-700">
                  {targetIdentifier || "votre adresse"}
                </span>
              </p>
            </div>

            <Form {...resetForm}>
              <form
                onSubmit={resetForm.handleSubmit(onResetSubmit)}
                className="space-y-5"
              >
                {/* OTP Input Centré */}
                <FormField
                  control={resetForm.control}
                  name="otp"
                  render={({ field }) => (
                    <FormItem className="flex flex-col items-center">
                      <FormControl>
                        <InputOTP maxLength={6} {...field}>
                          <InputOTPGroup>
                            <InputOTPSlot index={0} className="w-10 text-lg" />
                            <InputOTPSlot index={1} className="w-10 text-lg" />
                            <InputOTPSlot index={2} className="w-10 text-lg" />
                          </InputOTPGroup>
                          <div className="w-4" />
                          <InputOTPGroup>
                            <InputOTPSlot index={3} className="w-10 text-lg" />
                            <InputOTPSlot index={4} className="w-10 text-lg" />
                            <InputOTPSlot index={5} className="w-10 text-lg" />
                          </InputOTPGroup>
                        </InputOTP>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="space-y-3 pt-2">
                  <FormField
                    control={resetForm.control}
                    name="password"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Nouveau mot de passe</FormLabel>
                        <FormControl>
                          <Input
                            type="password"
                            {...field}
                            placeholder="Minimum 8 caractères"
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={resetForm.control}
                    name="confirmPassword"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Confirmer le mot de passe</FormLabel>
                        <FormControl>
                          <Input
                            type="password"
                            {...field}
                            placeholder="Répétez le mot de passe"
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <div className="flex flex-col gap-3 pt-2">
                  <Button type="submit" className="w-full" disabled={isLoading}>
                    {isLoading && (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    )}
                    Réinitialiser mon compte
                  </Button>

                  <div className="flex justify-between items-center text-sm mt-2">
                    <button
                      type="button"
                      onClick={() => setStep("request")}
                      className="flex items-center text-gray-500 hover:text-gray-800"
                    >
                      <ArrowLeft className="mr-1 h-3 w-3" /> Changer d'email
                    </button>

                    {/* BOUTON RENVOYER LOGIQUE */}
                    {cooldown > 0 ? (
                      <span className="text-gray-400 cursor-not-allowed flex items-center">
                        <Timer className="mr-1 h-3 w-3" /> Renvoyer (
                        {formatTime(cooldown)})
                      </span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => setStep("request")} // Retour step 1 pour renvoyer
                        className="text-primary hover:underline font-medium"
                      >
                        Renvoyer le code
                      </button>
                    )}
                  </div>
                </div>
              </form>
            </Form>
          </div>
        )}
      </div>
    </div>
  );
}
