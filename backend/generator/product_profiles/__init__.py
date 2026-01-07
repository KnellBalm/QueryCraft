# generator/product_profiles/__init__.py
"""Product Profile Strategy Pattern"""
from .base import BaseProductProfile
from .commerce import CommerceProfile
from .content import ContentProfile
from .saas import SaaSProfile
from .community import CommunityProfile
from .fintech import FintechProfile

PROFILE_MAP = {
    "commerce": CommerceProfile,
    "content": ContentProfile,
    "saas": SaaSProfile,
    "community": CommunityProfile,
    "fintech": FintechProfile,
}


def get_profile(product_type: str) -> BaseProductProfile:
    """Product Type에 맞는 Profile 인스턴스 반환"""
    profile_class = PROFILE_MAP.get(product_type, CommerceProfile)
    return profile_class()


__all__ = [
    "BaseProductProfile",
    "CommerceProfile",
    "ContentProfile",
    "SaaSProfile",
    "CommunityProfile",
    "FintechProfile",
    "get_profile",
    "PROFILE_MAP",
]
