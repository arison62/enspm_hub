// src/Pages/Profile/Edit.tsx
import { useRef, useState, useEffect } from "react";
import { router, usePage } from "@inertiajs/react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { ChevronsUpDown, Check, Trash2 } from "lucide-react";
import { toast } from "sonner";
import type {
  UserComplete,
  ExperienceProfessionnelleCreateOrUpdate,
  LienReseauSocialOut,
} from "@/types/user";
import axios from "@/lib/axios";
import type {
  PaysOut,
  ReferencesAcademiquesOut,
  ReseauSocialOut,
} from "@/types/base";
import { useAuthStore } from "@/stores/authStore";
import Axios from "axios";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { cn } from "@/lib/utils";
import { Checkbox } from "@/components/ui/checkbox";
import {
  NAV_EVENT_TYPE,
  useInternalNav,
} from "@/contexts/internal-nav-context";

gsap.registerPlugin(useGSAP);

export default function ProfileEdit() {
  const { navEmitter } = useInternalNav();
  const { user } = usePage().props as unknown as { user: UserComplete };
  const setUser = useAuthStore((state) => state.setUser);
  const profil = user.profil;

  const [basicInfo, setBasicInfo] = useState({
    nom_complet: profil.nom_complet || "",
    titre_id: profil.titre?.id || null,
    bio: profil.bio || null,
  });

  const [educationInfo, setEducationInfo] = useState({
    annee_sortie_id: profil.annee_sortie?.id || null,
    domaine_id: profil.domaine?.id || null,
  });

  const [contactInfo, setContactInfo] = useState({
    pays: profil.pays || null,
    ville: profil.ville || null,
    adresse: profil.adresse || null,
    telephone: profil.telephone || null,
  });

  const [experiences, setExperiences] = useState<
    ExperienceProfessionnelleCreateOrUpdate[]
  >(profil.experiences || []);
  const [newExp, setNewExp] = useState<ExperienceProfessionnelleCreateOrUpdate>(
    {
      titre_poste: "",
      nom_entreprise: "",
      lieu: "",
      date_debut: "",
      date_fin: "",
      description: "",
      est_poste_actuel: false,
    },
  );
  const [newLink, setNewLink] = useState<{ reseau_id: string; url: string }>({
    reseau_id: "",
    url: "",
  });
  const [socialLinks, setSocialLinks] = useState<LienReseauSocialOut[]>(
    profil.liens_reseaux || [],
  );
  const [availableReseaux, setAvailableReseaux] = useState<ReseauSocialOut[]>(
    [],
  );

  const [references, setReferences] = useState<ReferencesAcademiquesOut | null>(
    null,
  );
  const [countries, setCountries] = useState<PaysOut[]>([]);

  const [photo, setPhoto] = useState(profil.photo_profil);
  const [isLoading, setIsLoading] = useState({
    basic: false,
    education: false,
    contact: false,
    professional: false,
    links: false,
    photo: false,
    references: false,
    pays: false,
  });

  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    gsap.from(containerRef.current?.children || [], {
      opacity: 0,
      y: 20,
      stagger: 0.1,
      duration: 0.6,
      ease: "power2.out",
    });
  }, []);
  useEffect(() => {
    const handleOnPop = () => {
      router.reload({ only: ["user"] });
    };
    navEmitter.on(NAV_EVENT_TYPE.ON_POP, handleOnPop);
    return () => {
      navEmitter.off(NAV_EVENT_TYPE.ON_POP, handleOnPop);
    };
  });
  useEffect(() => {
    async function getReferencesAcademique() {
      setIsLoading((prev) => ({ ...prev, references: true }));
      try {
        const response = await axios.get("/references/academiques");
        if (response.status === 200) {
          const data = response.data as ReferencesAcademiquesOut;
          setReferences(data);
        }
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoading((prev) => ({ ...prev, references: false }));
      }
    }
    async function getAllCountries() {
      setIsLoading((prev) => ({ ...prev, countries: true }));
      try {
        const response = await axios.get("/references/pays");
        if (response.status === 200) {
          const data = response.data as PaysOut[];
          setCountries(data);
        }
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoading((prev) => ({ ...prev, countries: false }));
      }
    }
    async function getAvailableReseaux() {
      try {
        const response = await axios.get("/references/reseaux-sociaux");
        if (response.status === 200) {
          const data = response.data as ReseauSocialOut[];
          setAvailableReseaux(data);
        }
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoading((prev) => ({ ...prev, links: false }));
      }
    }
    getAllCountries();
    getReferencesAcademique();
    getAvailableReseaux();
  }, []);
  // Helper to submit section
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const submitSection = async (section: string, data: any) => {
    setIsLoading((prev) => ({ ...prev, [section]: true }));
    try {
      const response = await axios.put(`/users/${user.id}`, {
        profil: data,
      });

      if (response.status === 200) {
        setUser(response.data);
        toast.success("Mise à jour effectuée avec succès");
      }
    } catch (error) {
      if (Axios.isAxiosError(error)) {
        toast.error(
          error.response?.data?.detail ||
            "Une erreur s'est produite lors de la mise à jour.",
        );
      } else if (error instanceof Error) {
        toast.error("Une erreur s'est produite lors de la mise à jour.");
      }

      console.error(error);
    } finally {
      setIsLoading((prev) => ({ ...prev, [section]: false }));
    }
  };

  // Photo Upload (assuming endpoint POST /api/v1/users/{id}/photo)
  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setIsLoading((prev) => ({ ...prev, photo: true }));

    axios
      .post(`/users/${user.id}/photo`, formData)
      .then((response) => {
        if (response.status === 200) {
          setPhoto(response.data.photo_url);
          const updatedUser = {
            ...user,
            profil: { ...user.profil, photo_profil: response.data.photo_url },
          };
          setUser(updatedUser);
          setPhoto(response.data.photo_url);
          toast.success("Photo de profil mise à jour avec succès");
        }
      })
      .catch((error) => {
        console.error(error);
        toast.error(
          "Une erreur s'est produite lors de la mise à jour de la photo de profil.",
        );
      })
      .finally(() => {
        setIsLoading((prev) => ({ ...prev, photo: false }));
      });
  };

  const handleAddExperience = async () => {
    setIsLoading((prev) => ({ ...prev, professional: true }));
    try {
      // Remove empty values from newExp
      const cleanedNewExp = Object.fromEntries(
        Object.entries(newExp).filter(
          ([, v]) => v !== null && v !== "" && v !== undefined,
        ),
      );
      const response = await axios.post(
        `/users/experiences/${user.profil.id}`,
        cleanedNewExp,
      );
      if (response.status === 201) {
        setExperiences((prev) => [...prev, response.data]);
        setNewExp({
          titre_poste: "",
          nom_entreprise: "",
          lieu: "",
          date_debut: "",
          date_fin: "",
          description: "",
          est_poste_actuel: false,
        });
        toast.success("Expérience ajoutée avec succès");
      }
    } catch (error) {
      console.error(error);
      toast.error(
        "Une erreur s'est produite lors de l'ajout de l'expérience professionnelle.",
      );
    } finally {
      setIsLoading((prev) => ({ ...prev, professional: false }));
    }
  };
  const handleDeleteExperience = async (id: string) => {
    setIsLoading((prev) => ({ ...prev, professional: true }));
    try {
      const response = await axios.delete(`/users/experiences/${id}`);
      if (response.status === 204) {
        setExperiences((prev) =>
          prev.filter((experience) => experience.id !== id),
        );
        toast.success("Expérience supprimée avec succès");
      }
    } catch (error) {
      console.error(error);
      toast.error(
        "Une erreur s'est produite lors de la suppression de l'expérience professionnelle.",
      );
    } finally {
      setIsLoading((prev) => ({ ...prev, professional: false }));
    }
  };

  const handleAddSocialLink = async () => {
    if (!newLink.reseau_id || !newLink.url) return;

    setIsLoading((prev) => ({ ...prev, links: true }));
    try {
      const response = await axios.post(`/users/${user.id}/social-links`, {
        reseau_id: newLink.reseau_id, // L'ID du réseau sélectionné
        url: newLink.url,
      });
      setSocialLinks([...socialLinks, response.data]);
      setNewLink({ reseau_id: "", url: "" });
      toast.success("Réseau social ajouté");
    } catch (error) {
      console.error(error);
      toast.error("Erreur lors de l'ajout");
    } finally {
      setIsLoading((prev) => ({ ...prev, links: false }));
    }
  };

  const handleDeleteSocial = async (id: string) => {
    try {
      await axios.delete(`/users/${user.id}/social-links/${id}`);
      setSocialLinks(socialLinks.filter((l) => l.id !== id));
      toast.success("Lien supprimé");
    } catch (error) {
      console.error(error);
      toast.error("Erreur de suppression");
    }
  };
  return (
    <>
      <main
        ref={containerRef}
        className="container mx-auto flex-1 px-4 py-6 md:px-6 md:py-8 max-w-2xl lg:max-w-4xl"
      >
        <div className="space-y-8">
          {/* Photo de Profil */}
          <Card>
            <CardHeader>
              <CardTitle>Photo de Profil</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center gap-4">
              <Avatar className="size-32">
                <AvatarImage
                  src={photo || undefined}
                  alt="Photo de profil"
                  className="object-cover"
                />
                <AvatarFallback>{profil.nom_complet[0]}</AvatarFallback>
              </Avatar>
              <Label htmlFor="photo-upload">
                <Button variant="outline" disabled={isLoading.photo} asChild>
                  <span>
                    {isLoading.photo ? "Téléchargement..." : "Changer la photo"}
                  </span>
                </Button>
              </Label>
              <input
                id="photo-upload"
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handlePhotoUpload}
              />
            </CardContent>
          </Card>

          {/* Infos Basiques (Toujours ouvert) */}
          <Card>
            <CardHeader>
              <CardTitle>Informations Basiques</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="nom_complet">Nom Complet</Label>
                <Input
                  id="nom_complet"
                  value={basicInfo.nom_complet}
                  onChange={(e) =>
                    setBasicInfo({
                      ...basicInfo,
                      nom_complet: e.target.value,
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="titre">Titre</Label>

                <Select
                  onValueChange={(e) =>
                    setBasicInfo({ ...basicInfo, titre_id: e })
                  }
                  defaultValue={basicInfo.titre_id || ""}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Ajouter un titre" />
                  </SelectTrigger>
                  <SelectContent>
                    {references?.titres?.map((titre) => (
                      <SelectItem key={titre.id} value={titre.id}>
                        {titre.titre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="bio">Bio</Label>
                <Textarea
                  id="bio"
                  value={basicInfo.bio || undefined}
                  onChange={(e) =>
                    setBasicInfo({ ...basicInfo, bio: e.target.value })
                  }
                  rows={4}
                />
              </div>
              <Button
                onClick={() => submitSection("basic", basicInfo)}
                disabled={isLoading.basic}
              >
                {isLoading.basic
                  ? "Enregistrement..."
                  : "Enregistrer les infos basiques"}
              </Button>
            </CardContent>
          </Card>

          {/* Accordion pour sections secondaires */}
          <Accordion type="single" collapsible className="space-y-4">
            {/* Éducation */}
            {user.profil.statut_global == "alumni" && (
              <AccordionItem value="education">
                <AccordionTrigger>Éducation</AccordionTrigger>
                <AccordionContent className="space-y-6 pt-4">
                  <div className="space-y-2">
                    <Label htmlFor="annee_sortie">Promotion</Label>

                    <Select
                      onValueChange={(e) =>
                        setEducationInfo({
                          ...educationInfo,
                          annee_sortie_id: e,
                        })
                      }
                      defaultValue={educationInfo.annee_sortie_id || ""}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Votre promotion" />
                      </SelectTrigger>
                      <SelectContent>
                        {references?.annees_promotion?.map((annee_sortie) => (
                          <SelectItem
                            key={annee_sortie.id}
                            value={annee_sortie.id}
                          >
                            {annee_sortie.annee}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="domaine">Domaine</Label>

                    <Select
                      onValueChange={(e) =>
                        setEducationInfo({
                          ...educationInfo,
                          domaine_id: e,
                        })
                      }
                      defaultValue={educationInfo.domaine_id || ""}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Votre domaine" />
                      </SelectTrigger>
                      <SelectContent>
                        {references?.domaines?.map((domaine) => (
                          <SelectItem key={domaine.id} value={domaine.id}>
                            {domaine.nom}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    onClick={() => submitSection("education", educationInfo)}
                    disabled={isLoading.education}
                  >
                    {isLoading.education
                      ? "Enregistrement..."
                      : "Enregistrer l'éducation"}
                  </Button>
                </AccordionContent>
              </AccordionItem>
            )}

            {/* Contact */}
            <AccordionItem value="contact">
              <AccordionTrigger>Contact</AccordionTrigger>
              <AccordionContent className="space-y-6 pt-4">
                <div className="space-y-2">
                  <Label htmlFor="telephone">Téléphone</Label>
                  <Input
                    id="telephone"
                    value={contactInfo.telephone || undefined}
                    onChange={(e) =>
                      setContactInfo({
                        ...contactInfo,
                        telephone: e.target.value,
                      })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="pays">Pays</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        role="combobox"
                        className="w-[200px] justify-between"
                      >
                        {contactInfo.pays
                          ? countries.find(
                              (pays) => pays.code === contactInfo.pays,
                            )?.name
                          : "Veuillez choisir un pays"}
                        <ChevronsUpDown className="opacity-50" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-[200px] p-0">
                      <Command>
                        <CommandInput placeholder="Rechercher un pays..." />
                        <CommandList>
                          <CommandEmpty>Aucun pays trouvé</CommandEmpty>
                          <CommandGroup>
                            {countries.map((pays) => (
                              <CommandItem
                                key={pays.code}
                                value={pays.name}
                                onSelect={() => {
                                  setContactInfo({
                                    ...contactInfo,
                                    pays: pays.code,
                                  });
                                }}
                              >
                                {pays.name}
                                <Check
                                  className={cn(
                                    "ml-auto",
                                    contactInfo.pays == pays.code
                                      ? "opacity-100"
                                      : "opacity-0",
                                  )}
                                />
                              </CommandItem>
                            ))}
                          </CommandGroup>
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ville">Ville</Label>
                  <Input
                    id="ville"
                    value={contactInfo.ville || undefined}
                    onChange={(e) =>
                      setContactInfo({
                        ...contactInfo,
                        ville: e.target.value,
                      })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="adresse">Adresse Complet</Label>
                  <Input
                    id="adresse"
                    value={contactInfo.adresse || undefined}
                    onChange={(e) =>
                      setContactInfo({
                        ...contactInfo,
                        adresse: e.target.value,
                      })
                    }
                  />
                </div>

                <Button
                  onClick={() => submitSection("contact", contactInfo)}
                  disabled={isLoading.contact}
                >
                  {isLoading.contact
                    ? "Enregistrement..."
                    : "Enregistrer le contact"}
                </Button>
              </AccordionContent>
            </AccordionItem>

            {/* Professionnel */}
            <AccordionItem value="professional">
              <AccordionTrigger>Parcours Professionnel</AccordionTrigger>
              <AccordionContent className="space-y-6 pt-4">
                {/* Liste des expériences existantes */}
                <div className="space-y-4">
                  {experiences.length === 0 && (
                    <p className="text-sm text-muted-foreground italic">
                      Aucune expérience renseignée.
                    </p>
                  )}
                  {experiences.map((exp) => (
                    <div
                      key={exp.id}
                      className="flex justify-between items-start p-3 border rounded-lg bg-slate-50"
                    >
                      <div>
                        <h4 className="font-bold text-sm">{exp.titre_poste}</h4>
                        <p className="text-sm text-blue-600">
                          {exp.nom_entreprise}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(exp.date_debut).toLocaleDateString()} -{" "}
                          {exp.est_poste_actuel ? "Aujourd'hui" : exp.date_fin}
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          handleDeleteExperience(exp.id!);
                        }}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  ))}
                </div>

                {/* Formulaire d'ajout rapide ou Bouton déclencheur */}
                <div className="border-t pt-4">
                  <h3 className="text-sm font-medium mb-4">
                    Ajouter une expérience
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Titre du poste *</Label>
                      <Input
                        value={newExp.titre_poste}
                        onChange={(e) =>
                          setNewExp({ ...newExp, titre_poste: e.target.value })
                        }
                        placeholder="Ex: Ingénieur Logiciel"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Entreprise *</Label>
                      <Input
                        value={newExp.nom_entreprise}
                        onChange={(e) =>
                          setNewExp({
                            ...newExp,
                            nom_entreprise: e.target.value,
                          })
                        }
                        placeholder="Ex: Orange Cameroun"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Date de début *</Label>
                      <Input
                        type="date"
                        value={newExp.date_debut}
                        onChange={(e) =>
                          setNewExp({ ...newExp, date_debut: e.target.value })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Date de fin</Label>
                      <Input
                        type="date"
                        disabled={newExp.est_poste_actuel}
                        value={newExp.date_fin || ""}
                        onChange={(e) =>
                          setNewExp({ ...newExp, date_fin: e.target.value })
                        }
                      />
                    </div>
                    <div className="flex items-center space-x-2 md:col-span-2">
                      <Checkbox
                        id="current"
                        checked={newExp.est_poste_actuel}
                        onCheckedChange={(checked) =>
                          setNewExp({ ...newExp, est_poste_actuel: !!checked })
                        }
                      />
                      <Label htmlFor="current">C'est mon poste actuel</Label>
                    </div>
                    <div className="md:col-span-2 space-y-2">
                      <Label>Description</Label>
                      <Textarea
                        value={newExp.description || ""}
                        onChange={(e) =>
                          setNewExp({ ...newExp, description: e.target.value })
                        }
                        placeholder="Décrivez vos missions..."
                      />
                    </div>
                  </div>

                  <Button
                    className="mt-4"
                    disabled={
                      isLoading.professional ||
                      !newExp.titre_poste ||
                      !newExp.nom_entreprise
                    }
                    onClick={handleAddExperience}
                  >
                    {isLoading.professional
                      ? "Ajout en cours..."
                      : "Ajouter cette expérience"}
                  </Button>
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* Réseaux Sociaux */}
            <AccordionItem value="social">
              <AccordionTrigger>Réseaux Sociaux & Liens</AccordionTrigger>
              <AccordionContent className="space-y-6 pt-4">
                {/* Liste des liens existants */}
                <div className="grid grid-cols-1 gap-3">
                  {socialLinks.map((link) => (
                    <div
                      key={link.id}
                      className="flex items-center justify-between p-3 border rounded-md bg-slate-50"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="bg-white p-2 rounded shadow-sm font-bold text-blue-600">
                          {link.reseau.nom[0]}{" "}
                          {/* Initiale ou icône si dispo */}
                        </div>
                        <div>
                          <p className="text-sm font-medium">
                            {link.reseau.nom}
                          </p>
                          <a
                            href={link.url}
                            target="_blank"
                            className="text-xs text-blue-500 hover:underline truncate max-w-[200px] block"
                          >
                            {link.url}
                          </a>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteSocial(link.id!)}
                      >
                        <Trash2 className="h-4 w-4 text-red-400" />
                      </Button>
                    </div>
                  ))}
                </div>

                {/* Formulaire d'ajout */}
                <div className="space-y-4 pt-4 border-t">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Choisir un réseau</Label>
                      <Select
                        value={newLink.reseau_id}
                        onValueChange={(val) =>
                          setNewLink({ ...newLink, reseau_id: val })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Sélectionner..." />
                        </SelectTrigger>
                        <SelectContent>
                          {availableReseaux
                            // Filtrer pour ne pas proposer un réseau déjà ajouté
                            .filter(
                              (r) =>
                                !socialLinks.find(
                                  (sl) => sl.reseau.id === r.id,
                                ),
                            )
                            .map((r) => (
                              <SelectItem key={r.id} value={r.id!}>
                                {r.nom}
                              </SelectItem>
                            ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>URL du profil</Label>
                      <Input
                        type="url"
                        placeholder="https://..."
                        value={newLink.url}
                        onChange={(e) =>
                          setNewLink({ ...newLink, url: e.target.value })
                        }
                      />
                    </div>
                  </div>

                  <Button
                    className="w-full"
                    onClick={handleAddSocialLink}
                    disabled={
                      isLoading.links || !newLink.reseau_id || !newLink.url
                    }
                  >
                    {isLoading.links ? "Ajout..." : "Ajouter le réseau social"}
                  </Button>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      </main>
    </>
  );
}
