"""Internationalization: UI strings and large text blocks per language.

Canonical content language for translation is English (en).
Languages with full UI coverage: ru, en, de, es, fr.
Missing keys fall back to English.
"""

LANGS = ['en', 'ru', 'de', 'es', 'fr']        # all languages the pipeline supports
VISIBLE_LANGS = ['en', 'ru', 'es']            # shown in the switcher / built by default
LANG_NAMES = {'en': 'English', 'ru': 'Русский', 'de': 'Deutsch',
              'es': 'Español', 'fr': 'Français'}
DEFAULT_LANG = 'en'   # served at site root; others at /<lang>/

# ── short UI strings ──────────────────────────────────────────────────────────
UI = {
    'en': {
        'page_title': 'ML and Fuji Recipes',
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
        'articles_link': 'Articles →',
        'articles_title': 'Articles',
        'articles_sub': 'Notes on machine learning, evaluation and this project',
        'back_to_articles': '← All articles',
        'back_to_catalog': '← Recipe catalog',
        'lang_na': 'not available in this language — showing English',
    },
    'ru': {
        'page_title': 'ML и рецепты Fuji',
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
        'articles_link': 'Статьи →',
        'articles_title': 'Статьи',
        'articles_sub': 'Заметки про машинное обучение, оценку моделей и этот проект',
        'back_to_articles': '← Все статьи',
        'back_to_catalog': '← Каталог рецептов',
        'lang_na': 'нет перевода на этот язык — показан английский',
    },
    'es': {
        'page_title': 'ML y recetas Fuji',
        'header_h1': 'Las recetas de Fuji con ojos de ingeniero de ML',
        'header_sub': '191 recetas · 11 simulaciones de película · 24 grupos · clustering, análisis visual y búsqueda de similares',
        'comparison_title': 'Comparación de películas',
        'col_sim': 'Simulación',
        'cmp_contrast': 'Contraste',
        'cmp_saturation': 'Saturación',
        'cmp_colorcast': 'Dominante de color',
        'cmp_highlights': 'Altas luces',
        'cmp_shadows': 'Sombras',
        'cmp_bestfor': 'Ideal para',
        'cmp_grain': 'Grano',
        'bw_films': 'Películas monocromas',
        'settings': 'Ajustes',
        'recipes': 'Recetas',
        'visual_analysis': 'Análisis visual',
        'basis': 'Basada en:',
        'best_for_label': 'Ideal para:',
        'same': 'Igual:',
        'varies': 'Varía:',
        'recipes_word': 'recetas',
        'ext_note_pre': 'Las recetas de D’Agostino están marcadas con un asterisco',
        'ext_note_post': 'en las listas de grupos.',
        'official_credit': '© Fujifilm X',
        'articles_link': 'Artículos →',
        'articles_title': 'Artículos',
        'articles_sub': 'Notas sobre aprendizaje automático, evaluación y este proyecto',
        'back_to_articles': '← Todos los artículos',
        'back_to_catalog': '← Catálogo de recetas',
        'lang_na': 'no disponible en este idioma — se muestra en inglés',
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
