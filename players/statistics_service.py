"""
통계 분석 서비스 - 가설 검정 및 상관관계 분석

이 모듈은 Destiny 2 플레이어 데이터에 대한 통계적 분석을 제공합니다.
- 클래스별 빛 레벨 비교 (One-way ANOVA)
- 빛 레벨과 승리 점수 상관관계 (Pearson Correlation)
"""

import statistics as py_statistics
from typing import Optional
from datetime import datetime

from django.db.models import Max, Avg
from django.utils import timezone

try:
    from scipy import stats as scipy_stats
    import numpy as np
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    np = None

from .models import DestinyPlayer, DestinyCharacter


def class_light_level_anova() -> dict:
    """
    클래스별 빛 레벨 차이 검정 (One-way ANOVA).

    가설:
        H0: 클래스별 평균 빛 레벨에 차이가 없다
        H1: 클래스별 평균 빛 레벨에 차이가 있다

    Returns:
        dict: ANOVA 검정 결과
    """
    if not SCIPY_AVAILABLE:
        return {
            'error': 'scipy가 설치되지 않았습니다.',
            'test_name': 'One-way ANOVA',
            'available': False,
        }

    # 클래스별 빛 레벨 데이터 수집
    titan_levels = list(
        DestinyCharacter.objects.filter(
            class_type=0,
            light_level__gt=0
        ).values_list('light_level', flat=True)
    )
    hunter_levels = list(
        DestinyCharacter.objects.filter(
            class_type=1,
            light_level__gt=0
        ).values_list('light_level', flat=True)
    )
    warlock_levels = list(
        DestinyCharacter.objects.filter(
            class_type=2,
            light_level__gt=0
        ).values_list('light_level', flat=True)
    )

    # 데이터 유효성 검사
    if len(titan_levels) < 2 or len(hunter_levels) < 2 or len(warlock_levels) < 2:
        return {
            'error': '각 클래스에 최소 2개 이상의 데이터가 필요합니다.',
            'test_name': 'One-way ANOVA',
            'available': False,
            'groups': {
                'titan': {'n': len(titan_levels)},
                'hunter': {'n': len(hunter_levels)},
                'warlock': {'n': len(warlock_levels)},
            }
        }

    # ANOVA 검정 수행
    f_stat, p_value = scipy_stats.f_oneway(titan_levels, hunter_levels, warlock_levels)

    # 결과 생성
    alpha = 0.05
    significant = p_value < alpha

    return {
        'test_name': 'One-way ANOVA',
        'hypothesis': {
            'null': '클래스별 평균 빛 레벨에 차이가 없다 (H0)',
            'alternative': '클래스별 평균 빛 레벨에 차이가 있다 (H1)',
        },
        'groups': {
            'titan': {
                'n': len(titan_levels),
                'mean': round(np.mean(titan_levels), 2),
                'std': round(np.std(titan_levels, ddof=1), 2),
                'min': int(min(titan_levels)),
                'max': int(max(titan_levels)),
            },
            'hunter': {
                'n': len(hunter_levels),
                'mean': round(np.mean(hunter_levels), 2),
                'std': round(np.std(hunter_levels, ddof=1), 2),
                'min': int(min(hunter_levels)),
                'max': int(max(hunter_levels)),
            },
            'warlock': {
                'n': len(warlock_levels),
                'mean': round(np.mean(warlock_levels), 2),
                'std': round(np.std(warlock_levels, ddof=1), 2),
                'min': int(min(warlock_levels)),
                'max': int(max(warlock_levels)),
            },
        },
        'statistics': {
            'f_statistic': round(float(f_stat), 4),
            'p_value': round(float(p_value), 6),
            'alpha': alpha,
            'degrees_of_freedom': {
                'between': 2,  # k - 1 (3개 그룹 - 1)
                'within': len(titan_levels) + len(hunter_levels) + len(warlock_levels) - 3,
            },
        },
        'result': {
            'significant': significant,
            'interpretation': (
                '클래스별 빛 레벨에 통계적으로 유의한 차이가 있습니다.'
                if significant else
                '클래스별 빛 레벨에 통계적으로 유의한 차이가 없습니다.'
            ),
            'conclusion': 'H0 기각' if significant else 'H0 채택',
        },
        'available': True,
        'generated_at': timezone.now().isoformat(),
    }


def light_triumph_correlation() -> dict:
    """
    빛 레벨과 승리 점수 간 상관관계 분석 (Pearson Correlation).

    가설:
        H0: 빛 레벨과 승리 점수 사이에 상관관계가 없다 (ρ = 0)
        H1: 빛 레벨과 승리 점수 사이에 상관관계가 있다 (ρ ≠ 0)

    Returns:
        dict: Pearson 상관관계 분석 결과
    """
    if not SCIPY_AVAILABLE:
        return {
            'error': 'scipy가 설치되지 않았습니다.',
            'test_name': 'Pearson Correlation',
            'available': False,
        }

    # 플레이어별 최고 빛 레벨과 승리 점수 수집
    light_levels = []
    triumph_scores = []

    players = DestinyPlayer.objects.prefetch_related('characters').filter(
        active_triumph_score__gt=0
    )

    for player in players:
        max_light = player.characters.aggregate(max_light=Max('light_level'))['max_light']
        if max_light and max_light > 0:
            light_levels.append(max_light)
            triumph_scores.append(player.active_triumph_score)

    # 데이터 유효성 검사
    if len(light_levels) < 3:
        return {
            'error': '상관관계 분석을 위해 최소 3개 이상의 데이터가 필요합니다.',
            'test_name': 'Pearson Correlation',
            'available': False,
            'sample_size': len(light_levels),
        }

    # Pearson 상관관계 계산
    r, p_value = scipy_stats.pearsonr(light_levels, triumph_scores)

    # 상관 강도 해석
    abs_r = abs(r)
    if abs_r >= 0.7:
        strength = '강함'
        strength_en = 'strong'
    elif abs_r >= 0.4:
        strength = '중간'
        strength_en = 'moderate'
    elif abs_r >= 0.2:
        strength = '약함'
        strength_en = 'weak'
    else:
        strength = '거의 없음'
        strength_en = 'negligible'

    direction = '양의 상관 (정적 상관)' if r > 0 else '음의 상관 (부적 상관)'
    direction_en = 'positive' if r > 0 else 'negative'

    alpha = 0.05
    significant = p_value < alpha

    # 회귀선 계산 (시각화용)
    slope, intercept, _, _, std_err = scipy_stats.linregress(light_levels, triumph_scores)

    return {
        'test_name': 'Pearson Correlation',
        'hypothesis': {
            'null': '빛 레벨과 승리 점수 사이에 상관관계가 없다 (ρ = 0)',
            'alternative': '빛 레벨과 승리 점수 사이에 상관관계가 있다 (ρ ≠ 0)',
        },
        'sample_size': len(light_levels),
        'statistics': {
            'correlation_coefficient': round(float(r), 4),
            'r_squared': round(float(r ** 2), 4),
            'p_value': round(float(p_value), 6),
            'alpha': alpha,
        },
        'regression': {
            'slope': round(float(slope), 4),
            'intercept': round(float(intercept), 2),
            'std_error': round(float(std_err), 4),
        },
        'descriptive': {
            'light_level': {
                'mean': round(np.mean(light_levels), 2),
                'std': round(np.std(light_levels, ddof=1), 2),
                'min': int(min(light_levels)),
                'max': int(max(light_levels)),
            },
            'triumph_score': {
                'mean': round(np.mean(triumph_scores), 2),
                'std': round(np.std(triumph_scores, ddof=1), 2),
                'min': int(min(triumph_scores)),
                'max': int(max(triumph_scores)),
            },
        },
        'result': {
            'significant': significant,
            'strength': strength,
            'strength_en': strength_en,
            'direction': direction,
            'direction_en': direction_en,
            'interpretation': (
                f'빛 레벨과 승리 점수 사이에 통계적으로 유의한 {strength} {direction}이 있습니다. '
                f'(r = {r:.3f}, p = {p_value:.4f})'
                if significant else
                f'빛 레벨과 승리 점수 사이에 통계적으로 유의한 상관관계가 없습니다. '
                f'(r = {r:.3f}, p = {p_value:.4f})'
            ),
            'conclusion': 'H0 기각' if significant else 'H0 채택',
        },
        # 시각화용 데이터 (산점도)
        'scatter_data': {
            'x': light_levels,
            'y': triumph_scores,
            'x_label': '빛 레벨 (Light Level)',
            'y_label': '승리 점수 (Triumph Score)',
        },
        'available': True,
        'generated_at': timezone.now().isoformat(),
    }


def get_class_boxplot_data() -> dict:
    """
    클래스별 빛 레벨 박스플롯 데이터 생성.

    Returns:
        dict: Plotly 박스플롯용 데이터
    """
    class_data = {
        'titan': list(
            DestinyCharacter.objects.filter(
                class_type=0, light_level__gt=0
            ).values_list('light_level', flat=True)
        ),
        'hunter': list(
            DestinyCharacter.objects.filter(
                class_type=1, light_level__gt=0
            ).values_list('light_level', flat=True)
        ),
        'warlock': list(
            DestinyCharacter.objects.filter(
                class_type=2, light_level__gt=0
            ).values_list('light_level', flat=True)
        ),
    }

    return {
        'data': class_data,
        'labels': {
            'titan': '타이탄 (Titan)',
            'hunter': '헌터 (Hunter)',
            'warlock': '워록 (Warlock)',
        },
        'title': '클래스별 빛 레벨 분포',
        'x_label': '클래스',
        'y_label': '빛 레벨',
    }


def get_all_hypothesis_tests() -> dict:
    """
    모든 가설 검정 결과를 반환.

    Returns:
        dict: 모든 가설 검정 결과
    """
    return {
        'class_anova': class_light_level_anova(),
        'light_triumph_correlation': light_triumph_correlation(),
        'generated_at': timezone.now().isoformat(),
        'scipy_available': SCIPY_AVAILABLE,
    }
