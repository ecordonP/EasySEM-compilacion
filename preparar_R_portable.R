# Prepara la librería del R portable de EasySEM (carpeta R\ junto a sem.exe).
# Uso (lo llama preparar_R_portable.bat):  R\bin\Rscript.exe --vanilla preparar_R_portable.R
# Instala las últimas versiones binarias de CRAN en R\library, actualiza los paquetes
# recomendados, quita la documentación y escribe EASYSEM_R_MANIFEST.txt.
# También lo usan las compilaciones de macOS y Linux (GitHub Actions); en Linux, los binarios
# vienen de Posit Package Manager.

options(warn = 1, timeout = 600)
repos <- "https://cloud.r-project.org"
pkg_type <- "binary"
if (Sys.info()[["sysname"]] == "Linux") {
  # Linux: CRAN no publica binarios. Posit Package Manager sí (para la distribución de compilación)
  # si se identifica la versión de R en el User-Agent; lo que no tenga, se compila desde el código.
  repos <- Sys.getenv("EASYSEM_CRAN_REPO", "https://packagemanager.posit.co/cran/__linux__/jammy/latest")
  pkg_type <- "source"
  options(HTTPUserAgent = sprintf("R/%s R (%s)", getRversion(),
                                  paste(getRversion(), R.version$platform, R.version$arch, R.version$os)),
          Ncpus = max(1L, parallel::detectCores()))
}
lib <- normalizePath(file.path(R.home(), "library"), winslash = "/")
.libPaths(lib)   # solo la librería del portable

pkgs <- c(
  # Esenciales (CFAApp._R_REQUIRED_PACKAGES)
  "lavaan", "blavaan", "semTools", "misty", "mvnmle", "mice", "lavaan.mi", "semPlot", "lavaangui", "shiny",
  # Complementarias
  "lavaanExtra", "lavaanPlot", "MVN", "psych", "naniar", "car", "nonnest2", "haven", "ltm",
  "nortest", "performance", "effectsize", "mvoutlier", "MissMech", "coefficientalpha", "easystats",
  # Backend bayesiano JAGS (blavaan target = "jags")
  "rjags", "runjags"
)

cat("R:", R.version.string, "\nLibrería:", lib, "\n\n")
update.packages(lib.loc = lib, repos = repos, ask = FALSE, type = pkg_type, checkBuilt = TRUE)
install.packages(pkgs, lib = lib, repos = repos, type = pkg_type)
# Asegura las últimas versiones de todo lo instalado (dependencias incluidas)
update.packages(lib.loc = lib, repos = repos, ask = FALSE, type = pkg_type)

if (pkg_type == "source") {
  # Linux: rjags se compila contra el JAGS instalado en el equipo de compilación (el binario de
  # Posit Package Manager está enlazado con el JAGS de Ubuntu, que es una versión anterior)
  install.packages("rjags", lib = lib, repos = "https://cloud.r-project.org", type = "source")
}

not_installed <- function() {
  pkgs[!vapply(pkgs, function(p) requireNamespace(p, lib.loc = lib, quietly = TRUE), logical(1))]
}
# Reintentos: a veces CRAN publica el índice de una versión nueva antes que su binario (HTTP 404)
# y falla ese paquete y los que dependen de él. Se reintenta pasados unos minutos y, después,
# desde otros servidores de CRAN.
retry_repos <- unique(c(repos, "https://cloud.r-project.org", "https://cran.rstudio.com", "https://cran.r-project.org"))
for (attempt in seq_along(retry_repos)) {
  missing <- not_installed()
  if (!length(missing)) break
  cat("\nReintento", attempt, "desde", retry_repos[attempt], "para:", paste(missing, collapse = ", "), "\n")
  Sys.sleep(120)
  install.packages(missing, lib = lib, repos = retry_repos[attempt], type = pkg_type)
}
missing <- not_installed()
if (length(missing) && pkg_type == "binary" && Sys.info()[["sysname"]] == "Darwin") {
  # macOS: si el binario sigue sin publicarse (404 en todos los servidores), último intento
  # desde el código fuente; solo se compilan los paquetes (y dependencias) que faltan
  # Se incluyen las dependencias indirectas que falten (p. ej. xfun, que necesita knitr y este
  # semPlot): si no, el paquete se instala pero no carga
  db <- available.packages(repos = repos, type = "source")
  deps <- unique(unlist(tools::package_dependencies(missing, db = db, recursive = TRUE,
                                                    which = c("Depends", "Imports", "LinkingTo"))))
  ok <- function(p) requireNamespace(p, lib.loc = lib, quietly = TRUE)
  need <- c(Filter(function(p) p %in% rownames(db) && !ok(p), deps), missing)
  cat("\nÚltimo intento desde el código fuente para:", paste(need, collapse = ", "), "\n")
  install.packages(unique(need), lib = lib, repos = repos, type = "source")
  missing <- not_installed()
}
if (length(missing)) stop("No se han podido instalar: ", paste(missing, collapse = ", "))

# Quitar documentación (viñetas, HTML, pruebas, demos y ejemplos) para reducir tamaño
doc_dirs <- c("doc", "html", "tests", "demo", "examples")
removed <- 0
for (pkg_dir in list.dirs(lib, recursive = FALSE)) {
  for (d in file.path(pkg_dir, doc_dirs)) {
    if (dir.exists(d)) { unlink(d, recursive = TRUE); removed <- removed + 1 }
  }
}
for (d in file.path(R.home(), c("doc/manual", "tests"))) unlink(d, recursive = TRUE)
cat("\nCarpetas de documentación eliminadas:", removed, "\n")

ip <- installed.packages(lib.loc = lib)[, c("Package", "Version", "Built")]
writeLines(c(paste("EasySEM - R portable,", format(Sys.time(), "%Y-%m-%d")),
             R.version.string, "",
             sprintf("%-28s %-14s %s", ip[, "Package"], ip[, "Version"], ip[, "Built"])),
           file.path(R.home(), "EASYSEM_R_MANIFEST.txt"), useBytes = TRUE)
cat("Paquetes en la librería:", nrow(ip), "\nEASYSEM_OK\n")
