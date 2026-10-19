#!/bin/bash
# Comprueba el R y el JAGS portables de macOS con el entorno aislado que usa EasySEM.
# Se ejecuta con el R y el JAGS del sistema RETIRADOS (lo hace el flujo de GitHub Actions),
# para demostrar que el portable no depende de ellos.
#
# Uso:  bash mac/probar_R_portable_mac.sh <carpeta_con_R_y_JAGS>
set -euo pipefail
OUT="$(cd "$1" && pwd -P)"

env -i HOME="$HOME" PATH="$OUT/R/bin:$OUT/JAGS/bin:/usr/bin:/bin:/usr/sbin:/sbin" \
  R_HOME="$OUT/R" RHOME="$OUT/R" \
  R_LIBS_USER="$OUT/R/library" R_LIBS_SITE="$OUT/R/library" \
  R_ENVIRON_USER="$OUT/R/etc/Renviron.easysem" R_PROFILE_USER="$OUT/R/etc/Rprofile.easysem" \
  JAGS_HOME="$OUT/JAGS" \
  "$OUT/R/bin/Rscript" -e '
    cat("R.home():   ", normalizePath(R.home()), "\n")
    cat(".libPaths():", .libPaths(), "\n")
    stopifnot(normalizePath(R.home()) == normalizePath(Sys.getenv("R_HOME")))
    stopifnot(all(startsWith(normalizePath(.libPaths()), normalizePath(Sys.getenv("R_HOME")))))
    suppressMessages({ library(lavaan); library(semTools); library(blavaan) })
    fit <- cfa("visual =~ x1 + x2 + x3\ntextual =~ x4 + x5 + x6\nspeed =~ x7 + x8 + x9",
               data = HolzingerSwineford1939, estimator = "MLR")
    cat("AFC lavaan, CFI robusto:", round(fitMeasures(fit, "cfi.robust"), 4), "\n")
    options(jags.moddir = file.path(Sys.getenv("JAGS_HOME"), "lib", "JAGS", "modules-4"))
    suppressMessages(library(rjags))
    cat("JAGS:", as.character(rjags::jags.version()), "\n")
    runjags::runjags.options(jagspath = file.path(Sys.getenv("JAGS_HOME"), "bin", "jags"))
    # JAGS como programa independiente (runjags + jags-terminal), no solo como biblioteca (rjags)
    rj <- runjags::run.jags("model { for (i in 1:5) { y[i] ~ dnorm(mu, 1) } mu ~ dnorm(0, 0.01) }",
                            monitor = "mu", data = list(y = c(1, 2, 3, 2, 1)), n.chains = 2,
                            burnin = 200, sample = 200, method = "interruptible", silent.jags = TRUE)
    cat("runjags (jags-terminal), media de mu:", round(summary(rj)["mu", "Mean"], 2), "\n")
    bfit <- bcfa("visual =~ x1 + x2 + x3", data = HolzingerSwineford1939, target = "jags",
                 burnin = 300, sample = 300, n.chains = 2, seed = c(1, 2))
    cat("blavaan (JAGS):", round(coef(bfit)[1:2], 3), "\n")
    cat("EASYSEM_R_PORTABLE_OK\n")
  '
