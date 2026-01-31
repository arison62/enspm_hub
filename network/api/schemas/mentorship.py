from datetime import datetime
from typing import List, Optional
from ninja import ModelSchema, Schema
from pydantic import UUID4, field_validator
from network.models import MentorProfile, DemandeMentoring, RelationMentorat, SessionMentorat, FeedbackMentorat
from core.api.schemas import DomaineOut, FiliereOut


# ============================================
# SCHÉMAS MENTOR PROFILE
# ============================================

class MentorProfileOut(ModelSchema):
    """Schéma de sortie pour un profil mentor"""
    from users.api.schemas import ProfilBaseOut
    profil: ProfilBaseOut
    filieres_expertise: Optional[List[FiliereOut]] = None
    domaines_expertise: Optional[List[DomaineOut]] = None
    places_disponibles: int
    
    class Meta:
        model = MentorProfile
        fields = [
            'id', 'biographie', 'disponibilite',
            'nombre_max_mentees', 'est_actif',
            'nombre_demandes_recues', 'nombre_demandes_acceptees',
            'nombre_mentees_actuels',
            'created_at', 'updated_at'
        ]
    
    @staticmethod
    def resolve_places_disponibles(obj: MentorProfile) -> int:
        return obj.get_nombre_places_disponibles()


class MentorProfileCreate(Schema):
    """Schéma pour créer un profil mentor"""
    biographie: Optional[str] = None
    competences_cles: Optional[str] = None
    disponibilite: str
    nombre_max_mentees: int = 3
    filieres_expertise: Optional[List[UUID4]] = None
    domaines_expertise: Optional[List[UUID4]] = None
    
    @field_validator('nombre_max_mentees')
    @classmethod
    def validate_nombre_max(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError('Le nombre maximum de mentees doit être entre 1 et 10')
        return v


class MentorProfileUpdate(Schema):
    """Schéma pour mettre à jour un profil mentor"""
    biographie: Optional[str] = None
    competences_cles: Optional[str] = None
    disponibilite: Optional[str] = None
    nombre_max_mentees: Optional[int] = None
    est_actif: Optional[bool] = None
    filieres_expertise: Optional[List[UUID4]] = None
    domaines_expertise: Optional[List[UUID4]] = None
    
    @field_validator('nombre_max_mentees')
    @classmethod
    def validate_nombre_max(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 10):
            raise ValueError('Le nombre maximum de mentees doit être entre 1 et 10')
        return v




# ============================================
# SCHÉMAS DEMANDE MENTORING
# ============================================

class DemandeMentoringOut(ModelSchema):
    """Schéma de sortie pour une demande de mentoring"""
    from users.api.schemas import ProfilBaseOut
    mentee: ProfilBaseOut
    mentor_cible: Optional[MentorProfileOut] = None
    mentor_repondant: Optional[MentorProfileOut] = None
    filieres: Optional[List[FiliereOut]] = None
    domaines: Optional[List[DomaineOut]] = None
    est_expiree: bool
    
    class Meta:
        model = DemandeMentoring
        fields = [
            'id', 'message', 'objectifs', 'attentes',
            'disponibilite_souhaitee', 'format_prefere',
            'status', 'date_expiration',
            'reponse_message', 'reponse_date',
            'created_at', 'updated_at'
        ]
    
    @staticmethod
    def resolve_est_expiree(obj: DemandeMentoring) -> bool:
        return obj.est_expiree()


class DemandeMentoringCreate(Schema):
    """Schéma pour créer une demande de mentoring"""
    # Mode 1: Demande directe (mentor_cible)
    mentor_cible_id: Optional[UUID4] = None
    
    # Mode 2: Demande générale (filières + domaines)
    filieres_ids: Optional[List[UUID4]] = None
    domaines_ids: Optional[List[UUID4]] = None
    
    # Contenu obligatoire
    message: str
    objectifs: Optional[str] = None
    attentes: Optional[str] = None
    
    # Modalités
    disponibilite_souhaitee: Optional[str] = None
    format_prefere: Optional[str] = None
    
    @field_validator('mentor_cible_id')
    @classmethod
    def validate_mode_demande(cls, v, info):
        filieres = info.data.get('filieres_ids')
        domaines = info.data.get('domaines_ids')
        
        # Si mentor_cible est spécifié, filières et domaines doivent être None
        if v is not None:
            if filieres or domaines:
                raise ValueError(
                    'Une demande directe ne peut pas spécifier de filières ou domaines'
                )
        # Si mentor_cible n'est pas spécifié, au moins une filière ou un domaine doit l'être
        elif not filieres and not domaines:
            raise ValueError(
                'Une demande générale doit spécifier au moins une filière ou un domaine'
            )
        
        return v


class DemandeMentoringUpdate(Schema):
    """Schéma pour mettre à jour une demande (réservé au mentor)"""
    status: Optional[str] = None
    reponse_message: Optional[str] = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ['ACCEPTEE', 'REFUSEE', 'ANNULEE']:
            raise ValueError('Statut invalide. Choix: ACCEPTEE, REFUSEE, ANNULEE')
        return v
    



# ============================================
# SCHÉMAS RELATION MENTORAT
# ============================================

class RelationMentoratOut(ModelSchema):
    """Schéma de sortie pour une relation de mentorat"""
    from users.api.schemas import ProfilBaseOut
    mentor: MentorProfileOut
    mentee: ProfilBaseOut
    demande_origine: Optional[DemandeMentoringOut] = None
    duree_jours: int
    
    class Meta:
        model = RelationMentorat
        fields = [
            'id', 'objectifs', 'statut',
            'date_debut', 'date_fin_prevue', 'date_fin_reelle',
            'nombre_sessions', 'derniere_session',
            'created_at', 'updated_at'
        ]
    
    @staticmethod
    def resolve_duree_jours(obj: RelationMentorat) -> int:
        from datetime import date
        fin = obj.date_fin_reelle or date.today()
        debut = obj.date_debut
        return (fin - debut).days
    



class RelationMentoratCreate(Schema):
    """Schéma pour créer une relation (généralement via acceptation d'une demande)"""
    demande_id: UUID4
    objectifs: Optional[str] = None
    date_fin_prevue: Optional[str] = None


class RelationMentoratUpdate(Schema):
    """Schéma pour mettre à jour une relation"""
    objectifs: Optional[str] = None
    statut: Optional[str] = None
    date_fin_prevue: Optional[str] = None
    notes_privees_mentor: Optional[str] = None
    notes_privees_mentee: Optional[str] = None
    
    @field_validator('statut')
    @classmethod
    def validate_statut(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ['ACTIVE', 'EN_PAUSE', 'TERMINEE', 'ANNULEE']:
            raise ValueError('Statut invalide. Choix: ACTIVE, EN_PAUSE, TERMINEE, ANNULEE')
        return v


# ============================================
# SCHÉMAS SESSION MENTORAT
# ============================================

class SessionMentoratOut(ModelSchema):
    """Schéma de sortie pour une session de mentorat"""
    relation: RelationMentoratOut
    
    class Meta:
        model = SessionMentorat
        fields = [
            'id', 'date_prevue', 'duree_minutes', 'type_session', 'statut',
            'lieu_ou_lien', 'theme', 'objectifs_session',
            'date_reelle', 'duree_reelle_minutes', 'notes', 'actions_suivantes',
            'presence_mentee',
            'created_at', 'updated_at'
        ]


class SessionMentoratCreate(Schema):
    """Schéma pour créer une session"""
    relation_id: UUID4
    date_prevue: datetime
    duree_minutes: int = 60
    type_session: str = 'VIDEO'
    lieu_ou_lien: Optional[str] = None
    theme: Optional[str] = None
    objectifs_session: Optional[str] = None
    
    @field_validator('type_session')
    @classmethod
    def validate_type_session(cls, v: str) -> str:
        valid_types = ['VIDEO', 'TELEPHONE', 'CHAT', 'PHYSIQUE']
        if v not in valid_types:
            raise ValueError(f'Type de session invalide. Choix: {", ".join(valid_types)}')
        return v
    
    @field_validator('duree_minutes')
    @classmethod
    def validate_duree(cls, v: int) -> int:
        if v < 15 or v > 300:
            raise ValueError('La durée doit être entre 15 et 300 minutes')
        return v


class SessionMentoratUpdate(Schema):
    """Schéma pour mettre à jour une session"""
    date_prevue: Optional[datetime] = None
    duree_minutes: Optional[int] = None
    type_session: Optional[str] = None
    statut: Optional[str] = None
    lieu_ou_lien: Optional[str] = None
    theme: Optional[str] = None
    objectifs_session: Optional[str] = None
    notes: Optional[str] = None
    actions_suivantes: Optional[str] = None
    presence_mentee: Optional[bool] = None
    
    @field_validator('type_session')
    @classmethod
    def validate_type_session(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_types = ['VIDEO', 'TELEPHONE', 'CHAT', 'PHYSIQUE']
            if v not in valid_types:
                raise ValueError(f'Type de session invalide. Choix: {", ".join(valid_types)}')
        return v
    
    @field_validator('statut')
    @classmethod
    def validate_statut(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ['PLANIFIEE', 'REALISEE', 'ANNULEE', 'MANQUEE']:
            raise ValueError('Statut invalide. Choix: PLANIFIÉE, RÉALISÉE, ANNULÉE, MANQUÉE')
        return v


# ============================================
# SCHÉMAS FEEDBACK MENTORAT
# ============================================

class FeedbackMentoratOut(ModelSchema):
    """Schéma de sortie pour un feedback"""
    from users.api.schemas import ProfilBaseOut
    relation: RelationMentoratOut
    auteur: ProfilBaseOut
    
    class Meta:
        model = FeedbackMentorat
        fields = [
            'id', 'note', 'commentaires', 'recommanderait',
            'created_at', 'updated_at'
        ]


class FeedbackMentoratCreate(Schema):
    """Schéma pour créer un feedback"""
    relation_id: UUID4
    note: float
    commentaires: Optional[str] = None
    recommanderait: bool = True
    
    @field_validator('note')
    @classmethod
    def validate_note(cls, v: float) -> float:
        if v < 0.0 or v > 5.0:
            raise ValueError('La note doit être entre 0.0 et 5.0')
        return v

