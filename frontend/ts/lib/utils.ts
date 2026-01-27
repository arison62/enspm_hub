import { 
  differenceInMinutes, 
  differenceInHours, 
  differenceInDays, 
  differenceInWeeks, 
  differenceInMonths, 
  differenceInYears,
  parseISO
} from 'date-fns';
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getOportunityUrl(slug: string, type: "stage" | "emploi" | "formation") {
  switch (type) {
    case "stage":
      return `/internships/${slug}`
    case "emploi":
      return `/jobs/${slug}`
    case "formation":
      return `/trainings/${slug}`
  }
}

export function getAvatarFallback(name?: string) {
  if(!name) return ""
  return name
    .split(" ")
    .map((word) => word[0])
    .join("")
    .toUpperCase().slice(0, 2)
}


/**
 * Calcule la durée entre deux dates et la formate façon LinkedIn.
 * @param startDate - Date de début (Date ou string ISO)
 * @param endDate - Date de fin (optionnel, défaut à maintenant)
 * @returns string formatée (ex: "2 ans 3 mois", "5 j", "À l'instant")
 */
export const formatLinkedInDuration = (
  startDate: Date | string | null | undefined,
  endDate?: Date | string | null
): string | null => {
  if (!startDate) return null;

  const start = typeof startDate === 'string' ? parseISO(startDate) : startDate;
  const end = endDate 
    ? (typeof endDate === 'string' ? parseISO(endDate) : endDate) 
    : new Date();

  // On s'assure que la date de fin n'est pas antérieure au début pour éviter les durées négatives
  if (end < start) return "À l'instant";

  const mins = differenceInMinutes(end, start);
  if (mins < 1) return "À l'instant";
  if (mins < 60) return `${mins} min`;

  const hours = differenceInHours(end, start);
  if (hours < 24) return `${hours} h`;

  const days = differenceInDays(end, start);
  if (days < 7) return `${days} j`;

  const weeks = differenceInWeeks(end, start);
  if (days < 30) return `${weeks} sem`;

  const totalMonths = differenceInMonths(end, start);
  if (totalMonths < 12) return `${totalMonths} mois`;

  const years = differenceInYears(end, start);
  const remainingMonths = totalMonths % 12;

  const yearStr = `${years} an${years > 1 ? 's' : ''}`;
  
  if (remainingMonths > 0) {
    return `${yearStr} ${remainingMonths} mois`;
  }
  
  return yearStr;
};