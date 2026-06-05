args <- commandArgs(trailingOnly = TRUE)

input_a <- if (length(args) >= 1) args[[1]] else "final_results/15delt3_aav2_dimer_final_design_stats.csv"
input_b <- if (length(args) >= 2) args[[2]] else "final_results/pld1_final_design_stats.csv"
output_stub <- if (length(args) >= 3) args[[3]] else "final_results/af2_filter_comparison_clean"

dataset_a_name <- "15delt3_aav2_dimer"
dataset_b_name <- "pld1"

metrics <- data.frame(
  column = c(
    "Average_pLDDT",
    "Average_pTM",
    "Average_i_pTM",
    "Average_i_pAE",
    "Average_Binder_pLDDT",
    "Average_Binder_RMSD",
    "Average_Hotspot_RMSD",
    "Average_Target_RMSD"
  ),
  title = c(
    "Average pLDDT",
    "Average pTM",
    "Average interface pTM",
    "Average interface pAE",
    "Average binder pLDDT",
    "Average binder RMSD",
    "Average hotspot RMSD",
    "Average target RMSD"
  ),
  cutoff = c(0.80, 0.55, 0.50, 0.35, 0.80, 3.5, 6.0, NA),
  direction = c("higher", "higher", "higher", "lower", "higher", "lower", "lower", NA),
  scale_group = c("bounded", "bounded", "bounded", "bounded", "bounded", "rmsd", "rmsd", "rmsd"),
  stringsAsFactors = FALSE
)

read_score_table <- function(path) {
  df <- read.csv(path, stringsAsFactors = FALSE, check.names = FALSE)
  if ("Rank" %in% names(df)) {
    rank_num <- suppressWarnings(as.numeric(df$Rank))
    keep <- is.finite(rank_num)
    if (any(keep)) {
      df <- df[keep, , drop = FALSE]
    }
  }
  df
}

to_numeric <- function(x) {
  suppressWarnings(v <- as.numeric(x))
  v[is.finite(v)]
}

draw_density_shape <- function(values, center, width, fill, border) {
  values <- values[is.finite(values)]
  if (length(values) < 2) return(invisible(NULL))

  d <- density(values, n = 512, adjust = 1.1)
  w <- d$y / max(d$y) * width

  polygon(
    x = c(center - w, rev(center + w)),
    y = c(d$x, rev(d$x)),
    col = adjustcolor(fill, alpha.f = 0.18),
    border = NA
  )

  lines(center - w, d$x, col = border, lwd = 1.4)
  lines(center + w, d$x, col = border, lwd = 1.4)
}

draw_group <- function(values, center, point_col, line_col) {
  points(
    jitter(rep(center, length(values)), amount = 0.05),
    values,
    pch = 1,
    cex = 0.72,
    lwd = 0.45,
    col = adjustcolor(point_col, alpha.f = 0.85)
  )

  boxplot(
    values,
    at = center,
    add = TRUE,
    axes = FALSE,
    outline = FALSE,
    boxwex = 0.16,
    col = "white",
    border = line_col,
    lwd = 0.55,
    medcol = line_col,
    whiskcol = line_col,
    staplewex = 0.5
  )
}

draw_direction_note <- function(direction) {
  if (is.na(direction) || !nzchar(direction)) return(invisible(NULL))
  usr <- par("usr")
  text_x <- usr[1] + 0.04 * diff(usr[1:2])
  text_y <- usr[4] - 0.08 * diff(usr[3:4])
  label <- if (direction == "higher") "Higher is better" else "Lower is better"
  col <- if (direction == "higher") "#1B7F5A" else "#B85C38"
  text(text_x, text_y, labels = label, adj = c(0, 1), cex = 0.82, font = 2, col = col)
}

draw_reference_note <- function(label) {
  usr <- par("usr")
  text_x <- usr[1] + 0.04 * diff(usr[1:2])
  text_y <- usr[4] - 0.08 * diff(usr[3:4])
  text(text_x, text_y, labels = label, adj = c(0, 1), cex = 0.82, font = 2, col = "#6B7280")
}

plot_panel <- function(values_a, values_b, title, cutoff, direction, scale_group, colors) {
  all_vals <- c(values_a, values_b, cutoff)
  if (scale_group == "bounded") {
    ylim <- c(0, 1)
    axis_ticks <- seq(0, 1, by = 0.2)
  } else {
    r <- range(all_vals, finite = TRUE)
    ymax <- max(all_vals, na.rm = TRUE)
    pad_top <- max(diff(r) * 0.12, if (ymax <= 5) 0.2 else 0.5)
    ylim <- c(0, ymax + pad_top)
    axis_ticks <- pretty(ylim, n = 5)
  }

  plot(
    NA,
    xlim = c(0.55, 2.45),
    ylim = ylim,
    xaxt = "n",
    yaxt = "n",
    xlab = "",
    ylab = "",
    main = title,
    cex.main = 1.02,
    bty = "n"
  )

  abline(h = axis_ticks, col = "#EEF2F5", lwd = 0.5)
  axis(2, at = axis_ticks, las = 1, cex.axis = 0.82, lwd = 0, lwd.ticks = 0.5, col.ticks = "#9099A1")
  axis(
    1,
    at = c(1, 2),
    labels = c(
      paste0("15delt3\nn=", length(values_a)),
      paste0("pld1\nn=", length(values_b))
    ),
    tick = FALSE,
    cex.axis = 0.84,
    line = -0.5
  )

  draw_group(values_a, 1, point_col = colors[1], line_col = colors[1])
  draw_group(values_b, 2, point_col = colors[2], line_col = colors[2])

  if (is.finite(cutoff)) {
    abline(h = cutoff, col = "#C33A36", lwd = 1.1, lty = 2)
    label_x <- 2.38
    label_pos <- if (!is.na(direction) && direction == "higher") 1 else 3
    text(
      label_x,
      cutoff,
      labels = paste0("cutoff ", if (!is.na(direction) && direction == "higher") ">=" else "<=", " ", cutoff),
      pos = label_pos,
      cex = 0.72,
      col = "#9F2D2A",
      font = 2,
      offset = 0.35
    )
    draw_direction_note(direction)
  } else {
    draw_reference_note("No documented cutoff")
  }

  box(col = "#D6DCE2", lwd = 0.6)
}

render_plot <- function(device_fun, ...) {
  device_fun(...)
  on.exit(dev.off(), add = TRUE)

  op <- par(
    mfrow = c(2, 4),
    mar = c(3.6, 3.9, 2.4, 1.1),
    oma = c(2.4, 0.4, 3.1, 0.2),
    family = "sans",
    lend = "round",
    ljoin = "round"
  )
  on.exit(par(op), add = TRUE)

  colors <- c("#4C84C4", "#D88C3A")

  for (i in seq_len(nrow(metrics))) {
    values_a <- to_numeric(data_a[[metrics$column[i]]])
    values_b <- to_numeric(data_b[[metrics$column[i]]])
    plot_panel(values_a, values_b, metrics$title[i], metrics$cutoff[i], metrics$direction[i], metrics$scale_group[i], colors)
  }

  par(fig = c(0, 1, 0, 1), oma = c(0, 0, 0, 0), mar = c(0, 0, 0, 0), new = TRUE, xpd = NA)
  plot.new()
  legend(
    x = 0.5,
    y = 0.06,
    legend = c("15delt3_aav2_dimer", "pld1", "Documented cutoff", "No documented cutoff"),
    pch = c(1, 1, NA, NA),
    lty = c(NA, NA, 2, NA),
    lwd = c(NA, NA, 2, NA),
    col = c(colors[1], colors[2], "#C33A36", "#6B7280"),
    pt.cex = 1.2,
    bty = "n",
    cex = 0.95,
    xjust = 0.5,
    yjust = 0.5,
    horiz = TRUE
  )
  text(
    0.5,
    0.025,
    labels = "Bounded AF2 metrics use a fixed 0 to 1 axis; RMSD panels start at 0 and use natural scales. Target RMSD is shown for reference only.",
    cex = 0.86
  )

  mtext(
    "BindCraft AF2 Confidence Filter Comparison",
    side = 3,
    outer = TRUE,
    line = 1.2,
    cex = 1.35,
    font = 2
  )
  mtext(
    "Five bounded AF2 metrics share a fixed 0 to 1 axis; RMSD panels remain on interpretable natural scales",
    side = 3,
    outer = TRUE,
    line = 0.1,
    cex = 0.95
  )
}

data_a <- read_score_table(input_a)
data_b <- read_score_table(input_b)
png_type <- if (capabilities("cairo")) "cairo" else "Xlib"

render_plot(
  png,
  filename = paste0(output_stub, ".png"),
  width = 4400,
  height = 2500,
  res = 400,
  type = png_type,
  bg = "white"
)

render_plot(
  pdf,
  file = paste0(output_stub, ".pdf"),
  width = 15,
  height = 8.5,
  useDingbats = FALSE,
  bg = "white"
)

render_plot(
  svg,
  filename = paste0(output_stub, ".svg"),
  width = 15,
  height = 8.5,
  bg = "white"
)

message("Wrote: ", paste0(output_stub, ".png"))
message("Wrote: ", paste0(output_stub, ".pdf"))
message("Wrote: ", paste0(output_stub, ".svg"))
