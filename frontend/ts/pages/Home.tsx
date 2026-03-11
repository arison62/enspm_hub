import { Head } from "@inertiajs/react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  GraduationCap,
  Briefcase,
  Users,
  MessageCircle,
  Building2,
  Calendar,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";
import enspmLogo from "@/assets/enspm-logo.png";

export default function Home() {
  const features = [
    {
      icon: Briefcase,
      title: "Opportunités Professionnelles",
      description:
        "Accédez à des offres de stage et d'emploi exclusives postées par nos partenaires et alumni.",
    },
    {
      icon: Users,
      title: "Réseau Alumni",
      description:
        "Connectez-vous avec des anciens diplômés, partagez votre expérience et développez votre réseau.",
    },
    {
      icon: GraduationCap,
      title: "Formations Continues",
      description:
        "Découvrez des formations et séminaires pour enrichir vos compétences et faire évoluer votre carrière.",
    },
    {
      icon: MessageCircle,
      title: "Communauté Active",
      description:
        "Rejoignez des groupes de discussion, échangez des idées et collaborez sur des projets innovants.",
    },
    {
      icon: Building2,
      title: "Organisations Partenaires",
      description:
        "Suivez les entreprises et institutions partenaires pour ne manquer aucune opportunité.",
    },
    {
      icon: Calendar,
      title: "Événements & Rencontres",
      description:
        "Participez à des événements networking, conférences et rencontres professionnelles.",
    },
  ];

  const stats = [
    { value: "500+", label: "Alumni Actifs" },
    { value: "200+", label: "Offres Publiées" },
    { value: "50+", label: "Partenaires" },
    { value: "30+", label: "Groupes" },
  ];

  return (
    <>
      <Head title="Bienvenue sur ENSPM Hub" />

      <div className="min-h-screen flex flex-col bg-background">
        {/* Header */}
        <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
          <div className="container mx-auto px-4 h-16 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded flex items-center justify-center">
                <img src={enspmLogo} alt="" />
              </div>
              <span className="text-xl font-semibold text-foreground">
                ENSPM Hub
              </span>
            </div>

            <Button asChild variant="default" size="sm">
              <a href="/login">Se connecter</a>
            </Button>
          </div>
        </header>

        {/* Hero Section */}
        <section className="flex-1 flex items-center justify-center py-20 px-4">
          <div className="container mx-auto max-w-6xl">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              {/* Left Content */}
              <div className="space-y-6">
                <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-foreground leading-tight">
                  Votre réseau professionnel{" "}
                  <span className="text-primary">commence ici</span>
                </h1>

                <p className="text-lg text-muted-foreground max-w-lg">
                  ENSPM Hub connecte les alumni, étudiants et partenaires de
                  l'École Nationale Supérieure Polytechnique de Maroua.
                  Développez votre carrière, partagez vos expériences et
                  saisissez de nouvelles opportunités.
                </p>

                <div className="flex flex-col sm:flex-row gap-4 pt-4">
                  <Button asChild size="lg" className="gap-2">
                    <a href="/login">
                      Rejoindre la communauté
                      <ArrowRight className="w-4 h-4" />
                    </a>
                  </Button>
                  <Button asChild variant="outline" size="lg">
                    <a href="/login">Se connecter</a>
                  </Button>
                </div>

                <div className="flex items-center gap-2 text-sm text-muted-foreground pt-4">
                  <CheckCircle2 className="w-4 h-4 text-primary" />
                  <span>Accès gratuit pour tous les membres de l'ENSPM</span>
                </div>
              </div>

              {/* Right Content - Stats */}
              <div className="grid grid-cols-2 gap-4">
                {stats.map((stat, index) => (
                  <Card key={index} className="border-0 bg-muted/50">
                    <CardContent className="p-6 text-center">
                      <div className="text-3xl font-bold text-primary">
                        {stat.value}
                      </div>
                      <div className="text-sm text-muted-foreground mt-1">
                        {stat.label}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 px-4 bg-muted/30">
          <div className="container mx-auto max-w-6xl">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-foreground mb-4">
                Tout ce dont vous avez besoin pour avancer
              </h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Une plateforme complète conçue pour accompagner chaque étape de
                votre parcours professionnel
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feature, index) => {
                const Icon = feature.icon;
                return (
                  <Card
                    key={index}
                    className="border-0 bg-background hover:bg-muted/50 transition-colors"
                  >
                    <CardContent className="p-6">
                      <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                        <Icon className="w-6 h-6 text-primary" />
                      </div>
                      <h3 className="text-lg font-semibold text-foreground mb-2">
                        {feature.title}
                      </h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {feature.description}
                      </p>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 px-4">
          <div className="container mx-auto max-w-4xl">
            <Card className="border-0 bg-primary text-primary-foreground">
              <CardContent className="p-12 text-center">
                <h2 className="text-3xl font-bold mb-4">
                  Prêt à rejoindre votre réseau ?
                </h2>
                <p className="text-primary-foreground/80 mb-8 max-w-xl mx-auto">
                  Rejoignez des centaines d'alumni et d'étudiants qui utilisent
                  déjà ENSPM Hub pour développer leur carrière et rester
                  connectés avec l'école.
                </p>
                <Button asChild size="lg" variant="secondary" className="gap-2">
                  <a href="/login">
                    Connectez a votre compte
                    <ArrowRight className="w-4 h-4" />
                  </a>
                </Button>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t bg-background py-8 px-4 mt-auto">
          <div className="container mx-auto max-w-6xl">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded flex items-center justify-center">
                  <img src={enspmLogo} alt="" />
                </div>
                <span className="font-semibold text-foreground">ENSPM Hub</span>
              </div>

              <p className="text-sm text-muted-foreground text-center">
                © {new Date().getFullYear()} ENSPM Hub. Tous droits réservés.
                École Nationale Supérieure Polytechnique de Maroua.
              </p>

              <div className="flex items-center gap-6 text-sm text-muted-foreground">
                <a href="#" className="hover:text-foreground transition-colors">
                  Confidentialité
                </a>
                <a href="#" className="hover:text-foreground transition-colors">
                  Conditions
                </a>
                <a href="#" className="hover:text-foreground transition-colors">
                  Contact
                </a>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
