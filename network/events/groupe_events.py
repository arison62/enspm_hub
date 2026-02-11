from .base import BaseEvent
from uuid import UUID
from typing import Dict, Any, Optional
from datetime import datetime

class GroupeEvents:
    @staticmethod
    def utilisateur_ajoute(groupe_id: UUID, profil_id: UUID, data: Dict[str, Any]) -> BaseEvent:
        return BaseEvent.create(
            event_type='UtilisateurAjouteAuGroupe',
            aggregate_id=groupe_id,
            payload={
                'groupe_id': str(groupe_id),
                'profil_id': str(profil_id),
                'data': data
            }
        )

    @staticmethod
    def utilisateur_retire(groupe_id: UUID, profil_id: UUID, data: Dict[str, Any]) -> BaseEvent:
        return BaseEvent.create(
            event_type='UtilisateurRetireDuGroupe',
            aggregate_id=groupe_id,
            payload={
                'groupe_id': str(groupe_id),
                'profil_id': str(profil_id),
                'data': data
            }
        )

    @staticmethod
    def utilisateur_a_rejoint(groupe_id: UUID, profil_id: UUID, data: Dict[str, Any]) -> BaseEvent:
        return BaseEvent.create(
            event_type='UtilisateurARejointLeGroupe',
            aggregate_id=groupe_id,
            payload={
                'groupe_id': str(groupe_id),
                'profil_id': str(profil_id),
                'data': data
            }
        )

    @staticmethod
    def utilisateur_a_quitte(groupe_id: UUID, profil_id: UUID, data: Dict[str, Any]) -> BaseEvent:
        return BaseEvent.create(
            event_type='UtilisateurAQuitteLeGroupe',
            aggregate_id=groupe_id,
            payload={
                'groupe_id': str(groupe_id),
                'profil_id': str(profil_id),
                'data': data
            }
        )

    @staticmethod
    def groupe_cree(groupe_id: UUID, data: Dict[str, Any]) -> BaseEvent:
        return BaseEvent.create(
            event_type='GroupeCree',
            aggregate_id=groupe_id,
            payload={
                'groupe_id': str(groupe_id),
                'data': data
            }
        )

    @staticmethod
    def groupe_modifie(groupe_id: UUID, data: Dict[str, Any]) -> BaseEvent:
        return BaseEvent.create(
            event_type='GroupeModifie',
            aggregate_id=groupe_id,
            payload={
                'groupe_id': str(groupe_id),
                'data': data
            }
        )

    @staticmethod
    def groupe_ferme(groupe_id: UUID, data: Dict[str, Any]) -> BaseEvent:
        return BaseEvent.create(
            event_type='GroupeFerme',
            aggregate_id=groupe_id,
            payload={
                'groupe_id': str(groupe_id),
                'data': data
            }
        )

    @staticmethod
    def groupe_desactive(groupe_id: UUID, data: Dict[str, Any]) -> BaseEvent:
        return BaseEvent.create(
            event_type='GroupeDesactive',
            aggregate_id=groupe_id,
            payload={
                'groupe_id': str(groupe_id),
                'data': data
            }
        )

    @staticmethod
    def role_modifie(groupe_id: UUID, profil_id: UUID, data: Dict[str, Any]) -> BaseEvent:
        return BaseEvent.create(
            event_type='RoleUtilisateurModifie',
            aggregate_id=groupe_id,
            payload={
                'groupe_id': str(groupe_id),
                'profil_id': str(profil_id),
                'data': data
            }
        )
