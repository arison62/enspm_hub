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