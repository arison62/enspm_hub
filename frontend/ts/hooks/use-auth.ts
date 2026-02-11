import { useAuthStore } from "@/stores/authStore";

export const useAuth = () =>{
    const store = useAuthStore();

    return {
        user: store.user,
        profil: store.user?.profil,
        isAdmin: store.isAdmin,
        isAuthenticated: store.isAuthenticated,
        logout: store
    }
}