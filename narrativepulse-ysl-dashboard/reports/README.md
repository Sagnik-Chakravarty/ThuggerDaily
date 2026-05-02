# reports

Report drafting area.

## Contents

- `figures/`: generated visualizations for the written report.
- Future report outputs such as LaTeX, PDF, or exported notebooks.

The notebook in `notebooks/` is the primary source for generating report-ready figures.

## LaTeX Report

Main manuscript:

`narrativepulse_thuggerdaily_trial_report.tex`

Static figures:

`figures_png/`

Compile from this folder with a local LaTeX distribution:

```bash
pdflatex narrativepulse_thuggerdaily_trial_report.tex
pdflatex narrativepulse_thuggerdaily_trial_report.tex
```

Or upload `narrativepulse_thuggerdaily_trial_report.tex` and the `figures_png/` folder to Overleaf.

This workspace currently does not include a LaTeX engine such as `pdflatex`, `xelatex`, `latexmk`, or `tectonic`, so local PDF compilation is not available until one is installed.
