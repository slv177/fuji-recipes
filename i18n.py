"""Internationalization: UI strings and large text blocks per language.

Canonical content language for translation is English (en).
Languages with full UI coverage: ru, en, de, es, fr.
Missing keys fall back to English.
"""

LANGS = ['en', 'ru', 'de', 'es', 'fr']
LANG_NAMES = {'en': 'English', 'ru': 'Русский', 'de': 'Deutsch',
              'es': 'Español', 'fr': 'Français'}
DEFAULT_LANG = 'en'   # served at site root; others at /<lang>/

# ── short UI strings ──────────────────────────────────────────────────────────
UI = {
    'en': {
        'page_title': 'Fujifilm X-Trans IV recipes — film simulation groups',
        'header_h1': 'Fuji recipes through an ML engineer’s eyes',
        'header_sub': '191 recipes · 11 film simulations · 24 groups · clustering, visual analysis and similarity search',
        'comparison_title': 'Film comparison',
        'col_sim': 'Simulation',
        'cmp_contrast': 'Contrast',
        'cmp_saturation': 'Saturation',
        'cmp_colorcast': 'Color cast',
        'cmp_highlights': 'Highlights',
        'cmp_shadows': 'Shadows',
        'cmp_bestfor': 'Best for',
        'cmp_grain': 'Grain',
        'bw_films': 'Monochrome films',
        'settings': 'Settings',
        'recipes': 'Recipes',
        'visual_analysis': 'Visual analysis',
        'basis': 'Based on:',
        'best_for_label': 'Best for:',
        'same': 'Same:',
        'varies': 'Varies:',
        'groups_one': 'group',
        'groups_few': 'groups',
        'groups_many': 'groups',
        'recipes_word': 'recipes',
        'ext_note_pre': 'D’Agostino recipes are marked with an asterisk',
        'ext_note_post': 'in the recipe lists.',
        'official_credit': '© Fujifilm X',
    },
    'ru': {
        'page_title': 'Рецепты Fujifilm X-Trans IV — группы',
        'header_h1': 'Рецепты Fuji глазами ML-инженера',
        'header_sub': '191 рецепт · 11 плёночных симуляций · 24 группы · кластеризация, визуальный анализ и поиск похожих',
        'comparison_title': 'Сравнение плёнок',
        'col_sim': 'Симуляция',
        'cmp_contrast': 'Контраст',
        'cmp_saturation': 'Насыщенность',
        'cmp_colorcast': 'Цветовой сдвиг',
        'cmp_highlights': 'Светa',
        'cmp_shadows': 'Тени',
        'cmp_bestfor': 'Лучше всего для',
        'cmp_grain': 'Зерно',
        'bw_films': 'Монохромные плёнки',
        'settings': 'Настройки',
        'recipes': 'Рецепты',
        'visual_analysis': 'Визуальный анализ',
        'basis': 'Основа:',
        'best_for_label': 'Лучше всего для:',
        'same': 'Одинаково:',
        'varies': 'Варьируется:',
        'recipes_word': 'рецептов',
        'ext_note_pre': 'Рецепты Д’Агостино отмечены звёздочкой',
        'ext_note_post': 'в списках групп.',
        'official_credit': '© Fujifilm X',
    },
}


def t(lang, key):
    """Translate a UI key, falling back to English then to the key itself."""
    return UI.get(lang, {}).get(key) or UI['en'].get(key) or key


def plural_recipes(lang, n):
    """Return 'N recipes' phrase with correct grammar."""
    if lang == 'ru':
        if 2 <= n <= 4:
            word = 'рецепта'
        elif n == 1 or (n % 10 == 1 and n % 100 != 11):
            word = 'рецепт'
        else:
            word = 'рецептов'
        return f'{n} {word}'
    if lang == 'de':
        return f'{n} Rezept' if n == 1 else f'{n} Rezepte'
    if lang == 'es':
        return f'{n} receta' if n == 1 else f'{n} recetas'
    if lang == 'fr':
        return f'{n} recette' if n == 1 else f'{n} recettes'
    return f'{n} recipe' if n == 1 else f'{n} recipes'


def plural_groups(lang, n):
    if lang == 'ru':
        if n == 1:
            word = 'группа'
        elif 2 <= n <= 4:
            word = 'группы'
        else:
            word = 'групп'
        return f'{n} {word}'
    if lang == 'de':
        return f'{n} Gruppe' if n == 1 else f'{n} Gruppen'
    if lang == 'es':
        return f'{n} grupo' if n == 1 else f'{n} grupos'
    if lang == 'fr':
        return f'{n} groupe' if n == 1 else f'{n} groupes'
    return f'{n} group' if n == 1 else f'{n} groups'
