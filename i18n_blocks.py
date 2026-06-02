"""Large narrative HTML blocks (intro / ML / catalog) per language.

Each value is the full inner HTML of the intro section. English is canonical.
"""

BLOCKS = {}

# ── Russian (original) ────────────────────────────────────────────────────────
BLOCKS['ru'] = '''
<div class="intro-block lead">
  <h2>О проекте</h2>
  <p>Камеры Fujifilm умеют имитировать характер плёнки прямо при съёмке, а точную комбинацию
  настроек — «рецепт» — можно сохранить и переиспользовать. Любители по всему миру десятилетиями
  подбирают такие рецепты и делятся ими на тематических сайтах. Их накопились сотни.</p>

  <p>Мне пришла в голову мысль посмотреть на рецепты под углом <strong>машинного обучения</strong>.
  Если каждую настройку считать отдельным измерением, то каждый рецепт — это точка в многомерном
  пространстве. А к точкам в пространстве можно применить алгоритмы классификации и посмотреть,
  складываются ли они в осмысленные группы.</p>

  <p>Оказалось — складываются, и довольно отчётливо. Тогда возник следующий вопрос: а есть ли
  связь между этими группами и самими снимками? Моя гипотеза была, что у каждой группы рецептов
  есть своё узнаваемое <strong>настроение</strong> на фотографиях. Чтобы проверить, я передал
  языковой модели примеры снимков из каждой группы, а вместе с ними — текстовые описания, которые
  авторы прилагают к своим рецептам, и попросил найти закономерности.</p>

  <p class="lead-finding"><strong>Что получилось:</strong> гипотеза подтвердилась — но с оговоркой.
  У групп действительно читается общее настроение. Однако оно во многом наследуется от базовой
  плёночной симуляции, а не возникает само по себе от тонкой подстройки. Иначе говоря, «характер»
  задаёт прежде всего выбор плёнки, а рецепт лишь оттеняет его. Подробнее — ниже.</p>
</div>

<div class="intro-block">
  <h2>Как это устроено технически</h2>

  <p><strong>Каждая настройка — измерение.</strong> 14 параметров рецепта (Highlight, Shadow,
  Color, баланс белого, динамический диапазон, зерно и другие) задают оси пространства, а каждый
  рецепт становится точкой в нём. Перед анализом данные пришлось привести в порядок: свести
  синонимы (на разных камерах одна настройка называется по-разному), разложить составные поля
  (баланс белого → температура + сдвиги Red/Blue) и привести всё к сопоставимым масштабам.</p>

  <p><strong>Группировка.</strong> Рецепты сгруппированы методом иерархической кластеризации.
  Здесь обнаружилось главное: по одним числовым настройкам рецепты в чёткие группы
  <em>почти не делятся</em> — структуры в данных мало. Но стоит добавить признак «тип плёночной
  симуляции» — и группы становятся резкими и чистыми. Вывод: тип симуляции доминирует над тонкой
  подстройкой параметров. Внутри каждой симуляции мы затем нашли подгруппы — они различаются в
  основном балансом белого, динамическим диапазоном и чёткостью.</p>

  <p><strong>Связь со снимками.</strong> Для каждой группы примеры фотографий передавались
  мультимодальной модели, которая описывала сюжеты и настроение и отбирала самые характерные
  кадры. Параллельно из авторских текстов под рецептами извлекались ключевые слова, отличающие
  одну группу от других. На основе этих данных сгенерированы названия и описания групп.</p>

  <details class="ml-details">
    <summary>Технические детали</summary>
    <ul>
      <li><strong>Кластеризация:</strong> агломеративная, метод Уорда. Число групп выбрано по
      максимуму silhouette-метрики. Без учёта симуляции silhouette ≈ 0.09 (структуры практически
      нет); с one-hot-признаком симуляции — ≈ 0.46. Внутри симуляций silhouette подгрупп 0.11–0.24
      (границы размыты — настройки меняются скорее непрерывно, чем дискретными кластерами).</li>
      <li><strong>Понижение размерности:</strong> PCA и UMAP. Первые две компоненты PCA объясняют
      лишь ~26% дисперсии — признаки довольно независимы, поэтому для наглядных «карт» использовался
      нелинейный UMAP с добавлением симуляции как взвешенного признака.</li>
      <li><strong>Текстовый анализ:</strong> ключевые слова групп выделены через TF-IDF по авторским
      описаниям (термин, частый в одной группе и редкий в остальных, получает больший вес). Названия
      групп — тоже TF-IDF по названиям рецептов, чтобы «размазанные» по многим группам плёнки не
      доминировали.</li>
      <li><strong>Визуальный анализ:</strong> модель Claude (vision) на каждую группу.
      Поиск похожих рецептов — ближайшие соседи (евклидова метрика) в том же пространстве.</li>
    </ul>
  </details>
</div>

<div class="intro-block">
  <h2>О каталоге</h2>
  <p>Каталог построен на основе двух источников. Основной массив — <strong>184 рецепта</strong>
  с сайта <a href="https://fujixweekly.com/fujifilm-x-trans-iv-recipes/" target="_blank">Fuji X Weekly</a>
  (Ritchie Roesch), крупнейшей коллекции рецептов для X-Trans IV. Дополнительно добавлены
  <strong>7 рецептов</strong> Джозефа Д'Агостино
  (<a href="https://www.josephdagostinophotography.com/joedagostino-photo-blog/2021/1/27/r7ydnsoxgcgdi4uasfztt70yyuty1t" target="_blank">josephdagostinophotography.com</a>).
  Итого: <strong>191 рецепт</strong>. Ниже — таблица сравнения плёнок, а затем сами группы:
  у каждой описание, примеры снимков, типичные настройки и список входящих рецептов.</p>

  <h3>Что объединяет рецепты внутри группы, а что различает</h3>
  <p>Анализ разброса параметров внутри каждой группы показал устойчивую закономерность:
  <strong>баланс белого</strong> — самый вариативный параметр почти везде. Авторы приходят к
  похожему визуальному результату разными путями: кто-то через тёплый Kelvin, кто-то через сдвиги
  Red/Blue. <strong>Grain</strong>, напротив, обычно стабилен — внутри группы авторы сходятся на
  одном характере зернистости.</p>
  <p>Самая неоднородная группа — <strong>Kodak Contrast Classics</strong> (Acros): варьируется
  буквально всё, включая WB ±1375K. Это скорее «сборная всего разного в Acros», чем плотный
  кластер. Наоборот, <strong>Cinematic Teal Glow</strong> (Eterna) — единственная группа, где
  стабильна и Clarity = −5, и WB ≈ 4275K: оба автора пришли к практически одинаковому
  специфическому профилю независимо.</p>
  <p><strong>Kodachrome Warm Earth</strong> (Classic Chrome, 26 рецептов) — самая большая группа,
  и при этом ни один параметр не зафиксирован: это «размытый центр» симуляции, куда попало всё,
  что не вписалось в более специфичные подгруппы. Использовать как ориентир, но не как образец.</p>

  <h3>Рецепты Д'Агостино: насколько они уникальны?</h3>
  <p>Сравнение с ближайшими соседями в пространстве настроек показало следующее:</p>
  <ul>
    <li><strong>Kodachrome 64 +</strong> и <strong>Summer</strong> — практически идентичны уже
    существующим рецептам (расстояние 0.00 и 0.26). Независимые переоткрытия одних и тех же настроек.</li>
    <li><strong>Classic Negative</strong>, <strong>Kodachrome 64 −</strong>, <strong>Kodak Portra</strong> —
    вписываются в свои группы, но с личным акцентом: повышенная резкость, экстремально поднятые
    света, сильный тёплый сдвиг WB.</li>
    <li><strong>Noir</strong> (Acros) — выбивается из группы: Sharpness +4, Highlight +4, DR100.
    Намеренный максимализм контраста.</li>
    <li><strong>Monochrome</strong> — самый далёкий от любого соседа (расстояние 6.23), занимает
    собственную нишу в малочисленной группе.</li>
  </ul>
  <p class="intro-note">Рецепты Д'Агостино отмечены звёздочкой <span class="ext-mark">*</span>
  в списках групп.</p>
</div>'''

# ── English (canonical) ───────────────────────────────────────────────────────
BLOCKS['en'] = '''
<div class="intro-block lead">
  <h2>About the project</h2>
  <p>Fujifilm cameras can imitate the character of film right as you shoot, and the exact
  combination of settings — a “recipe” — can be saved and reused. Enthusiasts around the world
  have spent years dialing in such recipes and sharing them on dedicated sites. Hundreds have
  accumulated.</p>

  <p>It occurred to me to look at these recipes through the lens of <strong>machine learning</strong>.
  If each setting is treated as a separate dimension, then every recipe is a point in a
  multidimensional space — and you can run clustering algorithms on those points to see whether
  they fall into meaningful groups.</p>

  <p>They do — and quite distinctly. That raised the next question: is there a link between these
  groups and the photographs themselves? My hypothesis was that each group of recipes has its own
  recognizable <strong>mood</strong> in the resulting images. To test it, I fed a language model
  sample photos from each group along with the text descriptions authors attach to their recipes,
  and asked it to find patterns.</p>

  <p class="lead-finding"><strong>The finding:</strong> the hypothesis held up — with a caveat.
  Groups do share a common mood. But that mood is largely inherited from the base film simulation
  rather than emerging on its own from fine-tuning. In other words, “character” is set first and
  foremost by the choice of film; the recipe only shades it. More below.</p>
</div>

<div class="intro-block">
  <h2>How it works technically</h2>

  <p><strong>Each setting is a dimension.</strong> 14 recipe parameters (Highlight, Shadow, Color,
  white balance, dynamic range, grain and others) define the axes of the space, and each recipe
  becomes a point in it. Before analysis the data had to be cleaned up: merging synonyms (the same
  setting is named differently across cameras), decomposing composite fields (white balance →
  temperature + Red/Blue shifts) and rescaling everything to comparable ranges.</p>

  <p><strong>Grouping.</strong> Recipes were grouped with hierarchical clustering. The key
  discovery: on numeric settings alone the recipes <em>barely split</em> into clean groups — there
  is little structure in the data. But add the “film simulation type” feature and the groups
  become sharp and clean. Conclusion: the simulation type dominates over fine parameter tuning.
  Within each simulation we then found sub-groups — distinguished mainly by white balance, dynamic
  range and clarity.</p>

  <p><strong>The link to photographs.</strong> For each group, sample photos were passed to a
  multimodal model that described subjects and mood and selected the most representative frames.
  In parallel, keywords distinguishing one group from the others were extracted from the authors’
  recipe descriptions. Group names and descriptions were generated from this data.</p>

  <details class="ml-details">
    <summary>Technical details</summary>
    <ul>
      <li><strong>Clustering:</strong> agglomerative, Ward’s method. The number of groups was
      chosen by maximizing the silhouette score. Without the simulation feature, silhouette ≈ 0.09
      (almost no structure); with the one-hot simulation feature, ≈ 0.46. Within simulations,
      sub-group silhouette is 0.11–0.24 (fuzzy boundaries — settings vary continuously rather than
      in discrete clusters).</li>
      <li><strong>Dimensionality reduction:</strong> PCA and UMAP. The first two PCA components
      explain only ~26% of the variance — the features are fairly independent — so a nonlinear
      UMAP with the simulation added as a weighted feature was used for the visual “maps”.</li>
      <li><strong>Text analysis:</strong> group keywords were extracted via TF-IDF over the
      authors’ descriptions (a term frequent in one group and rare elsewhere gets more weight).
      Group names also use TF-IDF over recipe titles, so films “smeared” across many groups don’t
      dominate.</li>
      <li><strong>Visual analysis:</strong> a Claude (vision) model per group. Similarity search
      uses nearest neighbours (Euclidean metric) in the same space.</li>
    </ul>
  </details>
</div>

<div class="intro-block">
  <h2>About the catalog</h2>
  <p>The catalog is built from two sources. The main body — <strong>184 recipes</strong> from
  <a href="https://fujixweekly.com/fujifilm-x-trans-iv-recipes/" target="_blank">Fuji X Weekly</a>
  (Ritchie Roesch), the largest collection of X-Trans IV recipes. Added on top are
  <strong>7 recipes</strong> by Joseph D’Agostino
  (<a href="https://www.josephdagostinophotography.com/joedagostino-photo-blog/2021/1/27/r7ydnsoxgcgdi4uasfztt70yyuty1t" target="_blank">josephdagostinophotography.com</a>).
  Total: <strong>191 recipes</strong>. Below is a film comparison table, then the groups themselves:
  each with a description, sample photos, typical settings and the list of recipes it contains.</p>

  <h3>What unites recipes within a group, and what sets them apart</h3>
  <p>Analyzing the spread of parameters within each group revealed a consistent pattern:
  <strong>white balance</strong> is the most variable parameter almost everywhere. Authors reach a
  similar visual result by different routes — some via warm Kelvin, others via Red/Blue shifts.
  <strong>Grain</strong>, by contrast, is usually stable — within a group, authors converge on one
  grain character.</p>
  <p>The least homogeneous group is <strong>Kodak Contrast Classics</strong> (Acros): virtually
  everything varies, including WB ±1375K. It’s more of a “catch-all for everything Acros” than a
  tight cluster. Conversely, <strong>Cinematic Teal Glow</strong> (Eterna) is the only group where
  both Clarity = −5 and WB ≈ 4275K are stable: both authors arrived at nearly the same specific
  profile independently.</p>
  <p><strong>Kodachrome Warm Earth</strong> (Classic Chrome, 26 recipes) is the largest group, yet
  no single parameter is fixed: it’s the “blurry center” of the simulation, where everything that
  didn’t fit a more specific sub-group landed. Use as a reference point, not as a template.</p>

  <h3>The D’Agostino recipes: how unique are they?</h3>
  <p>Comparison with nearest neighbours in the settings space showed the following:</p>
  <ul>
    <li><strong>Kodachrome 64 +</strong> and <strong>Summer</strong> — practically identical to
    existing recipes (distance 0.00 and 0.26). Independent re-discoveries of the same settings.</li>
    <li><strong>Classic Negative</strong>, <strong>Kodachrome 64 −</strong>, <strong>Kodak Portra</strong> —
    fit their groups but with a personal accent: increased sharpness, extremely lifted highlights,
    a strong warm WB shift.</li>
    <li><strong>Noir</strong> (Acros) — stands out from its group: Sharpness +4, Highlight +4,
    DR100. Deliberate maximalism of contrast.</li>
    <li><strong>Monochrome</strong> — the farthest from any neighbour (distance 6.23), occupying
    its own niche in a small group.</li>
  </ul>
  <p class="intro-note">D’Agostino recipes are marked with an asterisk
  <span class="ext-mark">*</span> in the recipe lists.</p>
</div>'''


def blocks(lang):
    return BLOCKS.get(lang, BLOCKS['en'])
