"""
Fonte única de verdade para RBAC.

Perfis:
  ADMIN       — acesso total, único que gerencia usuários
  GESTOR      — acesso operacional completo (sem gestão de usuários)
  COLABORADOR — somente leitura
"""

from api.models.usuario import PerfilUsuario


def is_admin(perfil: str) -> bool:
    return perfil == PerfilUsuario.ADMIN


def is_gestor(perfil: str) -> bool:
    return perfil == PerfilUsuario.GESTOR


def is_colaborador(perfil: str) -> bool:
    return perfil == PerfilUsuario.COLABORADOR


def can_manage_users(perfil: str) -> bool:
    """Apenas ADMIN pode criar/editar/desativar usuários."""
    return is_admin(perfil)


def can_write_operational(perfil: str) -> bool:
    """ADMIN e GESTOR podem criar/editar/excluir dados operacionais."""
    return perfil in (PerfilUsuario.ADMIN, PerfilUsuario.GESTOR)


def can_view_data(perfil: str) -> bool:
    """Todos os perfis ativos podem visualizar."""
    return perfil in (PerfilUsuario.ADMIN, PerfilUsuario.GESTOR, PerfilUsuario.COLABORADOR)
