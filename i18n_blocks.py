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
    <summary>Технические детали (для любителей ML) — Развернуть</summary>
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

    <h4 class="ml-sub">Сходство поверх границ плёнок</h4>
    <p>Поиск похожих рецептов работает в пространстве, где тип плёночной симуляции — самый весомый
    признак, поэтому «соседями» почти всегда оказываются рецепты той же плёнки. Но если убрать
    симуляцию из вектора и сравнивать рецепты <strong>только по числовым настройкам</strong>,
    открывается скрытый слой: <strong>74% ближайших соседей оказываются из другой плёнки</strong>.</p>
    <p>Иначе говоря, под делением на симуляции есть второе измерение сходства — по «механике» рецепта.
    Например, McCurry Kodachrome (Classic Chrome) по чистым настройкам ближе к Velvia v2 и к рецептам
    на базе Superia, чем к большинству других Classic Chrome: их роднит тёплый баланс белого, высокий
    динамический диапазон и лёгкое зерно. Это прямое подтверждение главного вывода проекта —
    симуляция доминирует, но под ней живёт самостоятельная структура по настройкам.</p>
    <p>На этом слое начинают по-разному вести себя и сами метрики расстояния:</p>
    <ul>
      <li><strong>Евклидово расстояние</strong> (используется в поиске) даёт сбалансированный
      список — общая близость с акцентом на крупные расхождения.</li>
      <li><strong>Манхэттенское</strong> резко выделяет «почти точные совпадения» и обрывает
      остальных. Оно отвечает на вопрос «<em>сколько</em> настроек надо поменять», а не «насколько
      сильно» — удобно, чтобы найти рецепт, повторяющий нужный минимальной правкой.</li>
      <li><strong>Косинусное сходство</strong> игнорирует «силу» стиля и сравнивает только его
      направление. Оно находит родственников по характеру через границы плёнок — рецепты с тем же
      вектором отклонений (приглушённость, тёплый сдвиг), даже если базовая плёнка и интенсивность
      разные.</li>
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
    <summary>Technical details (for ML enthusiasts) — Expand</summary>
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

    <h4 class="ml-sub">Similarity across film boundaries</h4>
    <p>The similarity search works in a space where the film simulation type is the
    heaviest-weighted feature, so the “neighbours” are almost always recipes of the same film. But
    if you drop the simulation from the vector and compare recipes <strong>by numeric settings
    only</strong>, a hidden layer appears: <strong>74% of nearest neighbours turn out to be from a
    different film</strong>.</p>
    <p>In other words, beneath the split into simulations there is a second axis of similarity — the
    “mechanics” of a recipe. For example, McCurry Kodachrome (Classic Chrome) is, by raw settings,
    closer to Velvia v2 and to Superia-based recipes than to most other Classic Chrome recipes: they
    share a warm white balance, high dynamic range and light grain. This directly confirms the
    project’s central finding — the simulation dominates, but an independent structure by settings
    lives beneath it.</p>
    <p>On this layer the distance metrics themselves start to behave differently:</p>
    <ul>
      <li><strong>Euclidean distance</strong> (used in the search) gives a balanced list — overall
      closeness with an emphasis on large discrepancies.</li>
      <li><strong>Manhattan distance</strong> sharply isolates “near-exact matches” and drops off
      steeply for the rest. It answers “<em>how many</em> settings need to change”, not “by how
      much” — handy for finding the recipe that reproduces a given one with the smallest edit.</li>
      <li><strong>Cosine similarity</strong> ignores the “strength” of a style and compares only its
      direction. It finds relatives by character across film boundaries — recipes with the same
      deviation vector (muted, warm-shifted), even if the base film and the intensity differ.</li>
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


# ── Spanish ───────────────────────────────────────────────────────────────────
BLOCKS['es'] = '''
<div class="intro-block lead">
  <h2>Sobre el proyecto</h2>
  <p>Las cámaras Fujifilm pueden imitar el carácter de la película directamente al disparar, y la
  combinación exacta de ajustes — una «receta» — se puede guardar y reutilizar. Aficionados de todo
  el mundo llevan años afinando estas recetas y compartiéndolas en sitios especializados. Se han
  acumulado cientos.</p>

  <p>Se me ocurrió mirar estas recetas desde la óptica del <strong>aprendizaje automático</strong>.
  Si cada ajuste se trata como una dimensión independiente, entonces cada receta es un punto en un
  espacio multidimensional, y sobre esos puntos se pueden aplicar algoritmos de clasificación para
  ver si forman grupos con sentido.</p>

  <p>Y lo hacen — de forma bastante nítida. Eso planteó la siguiente pregunta: ¿existe una relación
  entre estos grupos y las propias fotografías? Mi hipótesis era que cada grupo de recetas tiene su
  propio <strong>estado de ánimo</strong> reconocible en las imágenes. Para comprobarlo, entregué a
  un modelo de lenguaje fotos de muestra de cada grupo junto con las descripciones de texto que los
  autores adjuntan a sus recetas, y le pedí que encontrara patrones.</p>

  <p class="lead-finding"><strong>El hallazgo:</strong> la hipótesis se confirmó — con un matiz.
  Los grupos sí comparten un estado de ánimo común. Pero ese carácter se hereda en gran medida de la
  simulación de película base, en lugar de surgir por sí solo del ajuste fino. Dicho de otro modo, el
  «carácter» lo define ante todo la elección de la película; la receta solo lo matiza. Más abajo, los
  detalles.</p>
</div>

<div class="intro-block">
  <h2>Cómo funciona técnicamente</h2>

  <p><strong>Cada ajuste es una dimensión.</strong> 14 parámetros de la receta (Highlight, Shadow,
  Color, balance de blancos, rango dinámico, grano y otros) definen los ejes del espacio, y cada
  receta se convierte en un punto. Antes del análisis hubo que ordenar los datos: unificar sinónimos
  (un mismo ajuste se llama distinto según la cámara), descomponer campos compuestos (balance de
  blancos → temperatura + desplazamientos Red/Blue) y reescalar todo a rangos comparables.</p>

  <p><strong>Agrupación.</strong> Las recetas se agruparon con clustering jerárquico. El hallazgo
  clave: solo con los ajustes numéricos las recetas <em>apenas se separan</em> en grupos limpios —
  hay poca estructura en los datos. Pero al añadir la característica «tipo de simulación de película»
  los grupos se vuelven nítidos y limpios. Conclusión: el tipo de simulación domina sobre el ajuste
  fino de parámetros. Dentro de cada simulación encontramos luego subgrupos — distinguidos sobre todo
  por el balance de blancos, el rango dinámico y la claridad.</p>

  <p><strong>El vínculo con las fotografías.</strong> Para cada grupo, las fotos de muestra se
  pasaron a un modelo multimodal que describió los temas y el estado de ánimo y seleccionó los
  fotogramas más representativos. En paralelo, se extrajeron de las descripciones de los autores las
  palabras clave que distinguen un grupo de los demás. Los nombres y descripciones de los grupos se
  generaron a partir de estos datos.</p>

  <details class="ml-details">
    <summary>Detalles técnicos (para aficionados al ML) — Desplegar</summary>
    <ul>
      <li><strong>Clustering:</strong> aglomerativo, método de Ward. El número de grupos se eligió
      maximizando la métrica silhouette. Sin la característica de simulación, silhouette ≈ 0,09 (casi
      sin estructura); con la característica one-hot de simulación, ≈ 0,46. Dentro de las
      simulaciones, el silhouette de los subgrupos es 0,11–0,24 (fronteras difusas — los ajustes
      varían de forma continua, no en clústeres discretos).</li>
      <li><strong>Reducción de dimensionalidad:</strong> PCA y UMAP. Las dos primeras componentes de
      PCA explican solo ~26% de la varianza — las características son bastante independientes — así
      que para los «mapas» visuales se usó un UMAP no lineal con la simulación añadida como
      característica ponderada.</li>
      <li><strong>Análisis de texto:</strong> las palabras clave de los grupos se extrajeron con
      TF-IDF sobre las descripciones de los autores (un término frecuente en un grupo y raro en los
      demás recibe más peso). Los nombres de los grupos también usan TF-IDF sobre los títulos de las
      recetas, para que las películas «repartidas» entre muchos grupos no dominen.</li>
      <li><strong>Análisis visual:</strong> un modelo Claude (visión) por grupo. La búsqueda de
      similares usa los vecinos más cercanos (métrica euclídea) en el mismo espacio.</li>
    </ul>

    <h4 class="ml-sub">Similitud más allá de las fronteras de película</h4>
    <p>La búsqueda de similares trabaja en un espacio donde el tipo de simulación de película es la
    característica de mayor peso, así que los «vecinos» son casi siempre recetas de la misma película.
    Pero si se quita la simulación del vector y se comparan las recetas <strong>solo por sus ajustes
    numéricos</strong>, aparece una capa oculta: <strong>el 74% de los vecinos más cercanos resultan
    ser de otra película</strong>.</p>
    <p>Dicho de otro modo, bajo la división por simulaciones hay un segundo eje de similitud — la
    «mecánica» de la receta. Por ejemplo, McCurry Kodachrome (Classic Chrome), por sus ajustes puros,
    está más cerca de Velvia v2 y de recetas basadas en Superia que de la mayoría de las demás Classic
    Chrome: comparten un balance de blancos cálido, un rango dinámico alto y grano ligero. Esto
    confirma directamente el hallazgo central del proyecto — la simulación domina, pero debajo vive
    una estructura independiente por ajustes.</p>
    <p>En esta capa, las propias métricas de distancia empiezan a comportarse de forma distinta:</p>
    <ul>
      <li><strong>Distancia euclídea</strong> (usada en la búsqueda) da una lista equilibrada —
      cercanía global con énfasis en las grandes discrepancias.</li>
      <li><strong>Distancia de Manhattan</strong> aísla con nitidez las «coincidencias casi exactas» y
      cae bruscamente para el resto. Responde a «<em>cuántos</em> ajustes hay que cambiar», no
      «cuánto» — útil para encontrar la receta que reproduce otra con la mínima edición.</li>
      <li><strong>Similitud del coseno</strong> ignora la «intensidad» de un estilo y compara solo su
      dirección. Encuentra parientes por carácter a través de las fronteras de película — recetas con
      el mismo vector de desviación (apagado, desplazado al cálido), aunque la película base y la
      intensidad sean distintas.</li>
    </ul>
  </details>
</div>

<div class="intro-block">
  <h2>Sobre el catálogo</h2>
  <p>El catálogo se construye a partir de dos fuentes. El grueso — <strong>184 recetas</strong> de
  <a href="https://fujixweekly.com/fujifilm-x-trans-iv-recipes/" target="_blank">Fuji X Weekly</a>
  (Ritchie Roesch), la mayor colección de recetas para X-Trans IV. A ellas se añaden
  <strong>7 recetas</strong> de Joseph D’Agostino
  (<a href="https://www.josephdagostinophotography.com/joedagostino-photo-blog/2021/1/27/r7ydnsoxgcgdi4uasfztt70yyuty1t" target="_blank">josephdagostinophotography.com</a>).
  Total: <strong>191 recetas</strong>. Debajo hay una tabla comparativa de películas y luego los
  grupos: cada uno con su descripción, fotos de muestra, ajustes típicos y la lista de recetas que
  contiene.</p>

  <h3>Qué une a las recetas de un grupo y qué las diferencia</h3>
  <p>Analizar la dispersión de parámetros dentro de cada grupo reveló un patrón constante: el
  <strong>balance de blancos</strong> es el parámetro más variable casi en todas partes. Los autores
  llegan a un resultado visual parecido por caminos distintos — unos con un Kelvin cálido, otros con
  desplazamientos Red/Blue. El <strong>grano</strong>, en cambio, suele ser estable — dentro de un
  grupo los autores convergen en un mismo carácter de grano.</p>
  <p>El grupo menos homogéneo es <strong>Kodak Contrast Classics</strong> (Acros): varía
  prácticamente todo, incluido el WB ±1375K. Es más un «cajón de sastre de todo lo Acros» que un
  clúster compacto. Por el contrario, <strong>Cinematic Teal Glow</strong> (Eterna) es el único grupo
  donde son estables tanto Clarity = −5 como WB ≈ 4275K: ambos autores llegaron casi al mismo perfil
  específico de forma independiente.</p>
  <p><strong>Kodachrome Warm Earth</strong> (Classic Chrome, 26 recetas) es el grupo más grande y,
  aun así, ningún parámetro está fijado: es el «centro difuso» de la simulación, donde acabó todo lo
  que no encajaba en un subgrupo más específico. Úsalo como referencia, no como plantilla.</p>

  <h3>Las recetas de D’Agostino: ¿qué tan únicas son?</h3>
  <p>La comparación con los vecinos más cercanos en el espacio de ajustes mostró lo siguiente:</p>
  <ul>
    <li><strong>Kodachrome 64 +</strong> y <strong>Summer</strong> — prácticamente idénticas a
    recetas ya existentes (distancia 0,00 y 0,26). Redescubrimientos independientes de los mismos
    ajustes.</li>
    <li><strong>Classic Negative</strong>, <strong>Kodachrome 64 −</strong>, <strong>Kodak Portra</strong> —
    encajan en sus grupos pero con un acento personal: más nitidez, altas luces muy levantadas, un
    fuerte desplazamiento cálido del WB.</li>
    <li><strong>Noir</strong> (Acros) — destaca de su grupo: Sharpness +4, Highlight +4, DR100.
    Maximalismo deliberado del contraste.</li>
    <li><strong>Monochrome</strong> — la más alejada de cualquier vecino (distancia 6,23), ocupa su
    propio nicho en un grupo pequeño.</li>
  </ul>
  <p class="intro-note">Las recetas de D’Agostino están marcadas con un asterisco
  <span class="ext-mark">*</span> en las listas de recetas.</p>
</div>'''


def blocks(lang):
    return BLOCKS.get(lang, BLOCKS['en'])
