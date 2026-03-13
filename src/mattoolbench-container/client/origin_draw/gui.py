import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from typing import Sequence, Optional, List
import os

# Try to import originpro; warn gracefully if not available
try:
    import originpro as op
    ORIGIN_AVAILABLE = True
except ImportError:
    ORIGIN_AVAILABLE = False
    print("Warning: originpro module not found. Run inside Origin or install the library first.")

class RamanPlotterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Raman Stacked Plotter for Origin")
        self.root.geometry("550x700")

        # Style
        style = ttk.Style()
        style.theme_use('clam')

        # --- Variable bindings ---
        self.var_lamda = tk.StringVar(value="ex: 532 nm")
        self.var_labels = tk.StringVar(value="GO, rGO, Annealed")
        self.var_colors = tk.StringVar(value="#EF0000, #FEC211, #3BC371")
        self.var_save_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop", "raman_stack.png"))

        self.var_is_2d = tk.BooleanVar(value=False)
        self.var_is_roman_ratio = tk.BooleanVar(value=True) # ID/IG ratio values
        self.var_is_ratio_mark = tk.BooleanVar(value=True)  # D/G/2D text marks
        self.var_is_peak_annotate = tk.BooleanVar(value=True) # Arrow
        self.var_is_peak_label = tk.BooleanVar(value=True) # Peak shift numbers
        self.var_label_style = tk.StringVar(value="horizontal")

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main_frame, text="Raman Stacked Spectrum Generator", font=("Helvetica", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # --- Basic settings ---
        grp_base = ttk.LabelFrame(main_frame, text="Basic Parameters", padding="10")
        grp_base.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)

        ttk.Label(grp_base, text="Excitation wavelength (Lamda):").grid(row=0, column=0, sticky="w")
        ttk.Entry(grp_base, textvariable=self.var_lamda, width=30).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(grp_base, text="Sample labels (comma-separated):").grid(row=1, column=0, sticky="w")
        ttk.Entry(grp_base, textvariable=self.var_labels, width=30).grid(row=1, column=1, sticky="w", padx=5)

        ttk.Label(grp_base, text="Color codes (comma-separated):").grid(row=2, column=0, sticky="w")
        ttk.Entry(grp_base, textvariable=self.var_colors, width=30).grid(row=2, column=1, sticky="w", padx=5)

        # --- Plot options ---
        grp_opts = ttk.LabelFrame(main_frame, text="Plot Options", padding="10")
        grp_opts.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)

        ttk.Checkbutton(grp_opts, text="Show 2D peak region (>2400 cm⁻¹)", variable=self.var_is_2d).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(grp_opts, text="Calculate and show ID/IG ratio", variable=self.var_is_roman_ratio).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(grp_opts, text="Annotate D/G/2D peak position lines", variable=self.var_is_ratio_mark).grid(row=2, column=0, sticky="w")
        ttk.Checkbutton(grp_opts, text="Draw G peak shift arrow", variable=self.var_is_peak_annotate).grid(row=3, column=0, sticky="w")
        ttk.Checkbutton(grp_opts, text="Annotate peak position values", variable=self.var_is_peak_label).grid(row=4, column=0, sticky="w")

        ttk.Label(grp_opts, text="Peak label orientation:").grid(row=5, column=0, sticky="w", pady=(5,0))
        ttk.Combobox(grp_opts, textvariable=self.var_label_style, values=["horizontal", "vertical"], state="readonly").grid(row=5, column=1, sticky="w", pady=(5,0))

        # --- Output settings ---
        grp_save = ttk.LabelFrame(main_frame, text="Output Settings", padding="10")
        grp_save.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)

        ttk.Entry(grp_save, textvariable=self.var_save_path).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(grp_save, text="Browse...", command=self.browse_file).pack(side=tk.RIGHT)

        # --- Run button ---
        btn_run = ttk.Button(main_frame, text="Generate Plot", command=self.run_process)
        btn_run.grid(row=4, column=0, columnspan=2, pady=20, ipady=10, sticky="ew")

    def browse_file(self):
        filename = filedialog.asksaveasfilename(defaultextension=".png",
                                              filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")])
        if filename:
            self.var_save_path.set(filename)

    def run_process(self):
        # 1. Read GUI parameters
        try:
            input_lamda = [self.var_lamda.get()]
            input_label_str = self.var_labels.get()
            input_label = [x.strip() for x in input_label_str.split(',') if x.strip()]

            input_colors_str = self.var_colors.get()
            input_colors = [x.strip() for x in input_colors_str.split(',') if x.strip()]

            save_path = self.var_save_path.get()

            is_2D_mark = self.var_is_2d.get()
            is_Roman_ratio = self.var_is_roman_ratio.get()
            is_Ratio__mark = self.var_is_ratio_mark.get()
            is_Peak_annotate = self.var_is_peak_annotate.get()
            is_Peak_label = self.var_is_peak_label.get()
            peak_label_style = self.var_label_style.get()

        except Exception as e:
            messagebox.showerror("Parameter Error", f"Failed to read parameters: {str(e)}")
            return

        # 2. Connect to Origin and read data
        if not ORIGIN_AVAILABLE:
            messagebox.showerror("Error", "Cannot import originpro library. Ensure Origin is installed and the Python environment is configured correctly.")
            return

        try:
            wks = op.find_sheet()
            if not wks:
                messagebox.showerror("Error", "No active Origin worksheet found.")
                return

            df = wks.to_df()

            if df.shape[1] < 6:
                messagebox.showwarning("Warning", f"Worksheet may have too few columns.\nCurrent columns: {df.shape[1]}\nScript needs columns 0, 1, 3, 5.")

            x = df.iloc[:, 0].values
            y1 = df.iloc[:, 1].values

            # Dynamically build y_list to avoid index errors
            y_list = [y1]
            if df.shape[1] > 3: y_list.append(df.iloc[:, 3].values)
            if df.shape[1] > 5: y_list.append(df.iloc[:, 5].values)

            # Pad colors if fewer than number of spectra
            while len(input_colors) < len(y_list):
                input_colors.append('#000000')

        except Exception as e:
            messagebox.showerror("Data Read Error", f"Failed to read data from Origin:\n{str(e)}")
            return

        # 3. Call core plotting logic
        try:
            self.execute_plotting_logic(
                x, y_list,
                input_lamda, input_label, input_colors,
                save_path,
                is_2D_mark, is_Roman_ratio, is_Ratio__mark,
                is_Peak_annotate, is_Peak_label, peak_label_style
            )
            messagebox.showinfo("Success", f"Plot generated successfully!\nFile saved to: {save_path}")
        except Exception as e:
            messagebox.showerror("Plot Error", f"An error occurred during plotting:\n{str(e)}")
            import traceback
            traceback.print_exc()

    # ==================== Core plotting logic ====================
    def execute_plotting_logic(self, x, y_list, lamda, label, colors, save_path,
                               is_2D_mark, is_Roman_ratio, is_Ratio__mark,
                               is_Peak_annotate, is_Peak_label, peak_label_style):

        def soft_scale(p_list, x_data, is_2D_mark=True):
            peaks = np.array(p_list)
            if len(peaks) == 0: raise ValueError("peaks_list cannot be empty!")
            if is_2D_mark==False:
                peaks = peaks[peaks < 2400]
                if len(peaks) == 0: peaks = np.array(p_list)
            center = peaks.mean()
            span = np.ptp(peaks)
            base_margin = span * 2.0
            total_width = span + 2 * base_margin
            extra_expand = total_width * 0.12
            xmin_raw = center - base_margin - extra_expand
            xmax_raw = center + base_margin + extra_expand
            x_low = np.percentile(x_data, 15)
            x_high = np.percentile(x_data, 85)
            xmin = min(x_low, xmin_raw)
            xmax = max(x_high, xmax_raw)
            if is_2D_mark==False and xmax > 2400: xmax = 2400
            return xmin, xmax

        def raman_ticks(xmin, xmax, is_2D_mark=True):
            width = xmax - xmin
            candidates = [50, 100, 150, 200, 250, 300, 400, 450, 500]
            best_step = 100
            best_score = float('inf')
            for step in candidates:
                n_ticks = int(width / step) + 1
                if 7 <= n_ticks <= 10: score = 0
                elif n_ticks < 7: score = 100 + (7 - n_ticks)
                else: score = 100 + (n_ticks - 10)
                if score < best_score:
                    best_score = score
                    best_step = step
            xmin_aligned = np.floor(xmin / best_step) * best_step
            xmax_aligned = np.ceil(xmax / best_step) * best_step
            if xmax_aligned - xmax > best_step: xmax_aligned -= best_step
            if xmin - xmin_aligned > best_step: xmin_aligned += best_step
            if not is_2D_mark and xmax_aligned > 2400: xmax_aligned = 2400
            return xmin_aligned, xmax_aligned, best_step

        def auto_offset(x, y_list, xmin=None, xmax=None, gap_ratio=0.25):
            y_list = [np.asarray(y) for y in y_list]
            n_spectra = len(y_list)
            if n_spectra == 0: raise ValueError("y_list cannot be empty!")
            if xmin is None or xmax is None:
                xmin_use = 200 if xmin is None else xmin
                xmax_use = 2800 if xmax is None else xmax
            else: xmin_use, xmax_use = xmin, xmax
            mask = (x >= xmin_use) & (x <= xmax_use)
            x_masked = x[mask]
            y_masked = [y[mask] for y in y_list]
            maxima = [y.max() for y in y_masked]
            minima = [y.min() for y in y_masked]
            shifts = [0.0]
            current_top = maxima[0]
            for i in range(1, n_spectra):
                required_shift = current_top - minima[i] + (maxima[0] * gap_ratio)
                shifts.append(required_shift)
                current_top = maxima[i] + required_shift
            y_shifted = [y_masked[i] + shifts[i] for i in range(n_spectra)]
            return x_masked, y_shifted, y_masked, shifts, maxima, minima

        def find_real_peak(x, y_list, prominence_ratio=0.15, edge_ignore=0.07):
            x = np.asarray(x)
            peaks_found = []
            start = int(len(x) * edge_ignore)
            end = int(len(x) * (1 - edge_ignore))
            x_mid = x[start:end]
            for y in y_list:
                y = np.asarray(y)
                y_mid = y[start:end]
                peaks, props = find_peaks(y_mid, prominence=y_mid.max() * prominence_ratio)
                if len(peaks) == 0:
                    best_pos = float(x_mid[np.argmax(y_mid)])
                else:
                    best_idx = peaks[np.argmax(props['prominences'])]
                    best_pos = float(x_mid[best_idx])
                peaks_found.append(best_pos)
            return peaks_found

        def calculate_raman_ratios(x, y_original_list, D_pos=1350, G_pos=1580, D2_pos=2700):
            def _intensity_at(y, pos):
                idx = np.argmin(np.abs(x - pos))
                return float(y[idx])
            ID_IG_list = []
            I2D_IG_list = []
            for y in y_original_list:
                y = np.asarray(y)
                I_D = _intensity_at(y, D_pos)
                I_G = _intensity_at(y, G_pos)
                I_2D = _intensity_at(y, D2_pos)
                ID_IG = I_D / I_G if I_G > 0 else 0.0
                I2D_IG = I_2D / I_G if I_G > 0 else 0.0
                ID_IG_list.append(round(ID_IG, 3))
                I2D_IG_list.append(round(I2D_IG, 3))
            return ID_IG_list, I2D_IG_list

        # --- Plotting logic ---
        p_list = find_real_peak(x, y_list)
        xmin, xmax = soft_scale(p_list, x, is_2D_mark=is_2D_mark)
        xmin, xmax, step = raman_ticks(xmin, xmax, is_2D_mark=is_2D_mark)
        [x_masked, y_shifted, y_masked, shifts, maxima, minima] = auto_offset(x, y_list, xmin=xmin, xmax=xmax, gap_ratio=0.25)

        y_shifted = [np.asarray(y) for y in y_shifted]
        n = len(y_shifted)

        plt.rcParams['font.family'] = 'Times New Roman'
        plt.close('all')  # Close previous figures to avoid memory leaks
        fig, ax = plt.subplots(figsize=(10, 8))

        for i, y in enumerate(y_shifted):
            c = colors[i % len(colors)]
            ax.plot(x_masked, y, color=c, linewidth=3)

        # X axis
        ax.set_xlim(xmin, xmax)
        ax.set_xticks(np.arange(xmin, xmax + 0.1, step))
        ax.tick_params(axis='x', labelsize=18, length=8, width=1.5)

        # Hide Y axis
        ax.set_yticks([])
        ax.tick_params(axis='y', left=False)
        for spine in ax.spines.values():
            spine.set_linewidth(1.5)

        # Y limits
        all_mins = [y.min() for y in y_shifted]
        all_maxs = [y.max() for y in y_shifted]
        first_height = all_maxs[0] - all_mins[0]
        extra_gap = first_height / 4
        bottom = min(all_mins) - extra_gap
        top = max(all_maxs) + 2 * extra_gap
        ax.set_ylim(bottom, top)

        ax.set_xlabel('Raman Shift (cm$^{-1}$)', fontsize=22, fontweight='bold', labelpad=12)
        ax.set_ylabel('Intensity (a.u.)', fontsize=22, fontweight='bold', labelpad=15)

        if lamda and len(lamda) > 0:
            ax.text(0.98, 0.94, lamda[0], transform=ax.transAxes, fontsize=20, fontweight='bold',
                    ha='right', va='top', color='black')

        # Sample labels
        if label and len(label) == n:
            ylim = ax.get_ylim()
            total_h = ylim[1] - ylim[0]
            for i, name in enumerate(label):
                c = colors[i % len(colors)]
                name_str = str(name).strip()
                if name_str and name_str.lower() not in ['none', 'nan', '']:
                    y_center = np.mean(y_shifted[i])
                    y_rel = (y_center - ylim[0]) / total_h
                    y_rel = np.clip(y_rel, 0.08, 0.92)
                    ax.text(0.02, y_rel, name_str, transform=ax.transAxes,
                            fontsize=20, fontweight='bold', color=c,
                            va='center', ha='left')

        ID_IG_vals, I2D_IG_vals = calculate_raman_ratios(x_masked, y_masked)

        # Ratio annotation
        if is_Roman_ratio and y_masked is not None:
            try:
                base_x = 0.02
                base_y = 0.98
                line_spacing = 0.06
                col_spacing = 0.07
                def color_for(i): return colors[i % len(colors)]

                ax.text(base_x, base_y, "Iᴅ/Iɢ =", transform=ax.transAxes,
                        fontsize=16, fontweight='bold', color='black', ha='left', va='top')
                current_x = base_x + 0.09
                for i, val in enumerate(ID_IG_vals):
                    ax.text(current_x, base_y, f"{val:>.3f}", transform=ax.transAxes,
                            fontsize=16, fontweight='bold', color=color_for(i), ha='left', va='top')
                    current_x += col_spacing

                if is_2D_mark:
                    ax.text(base_x, base_y - line_spacing, "I₂ᴅ/Iɢ =", transform=ax.transAxes,
                            fontsize=16, fontweight='bold', color='black', ha='left', va='top')
                    current_x = base_x + 0.09
                    for i, val in enumerate(I2D_IG_vals):
                        ax.text(current_x, base_y - line_spacing, f"{val:>.3f}", transform=ax.transAxes,
                                fontsize=16, fontweight='bold', color=color_for(i), ha='left', va='top')
            except Exception as e:
                print(f"Failed to annotate ID/IG ratios: {e}")

        # Peak lines
        peak_positions = [1350, 1580, 2700]
        peak_labels_txt = ['D', 'G', '2D']
        if is_Ratio__mark:
            for pos, lab in zip(peak_positions, peak_labels_txt):
                if lab == '2D' and not is_2D_mark: continue
                ax.axvline(pos, color='gray', linestyle='--', linewidth=1, alpha=0.7)
                ax.text(pos, 0.02, lab, transform=ax.get_xaxis_text1_transform(0)[0],
                        ha='center', va='bottom', fontsize=14, fontweight='bold', color='black')

        # G peak arrow
        if is_Peak_annotate:
            ax.annotate('', xy=(1580, 0.9), xytext=(1594, 0.9),
                        arrowprops=dict(arrowstyle='fancy', color='black', linewidth=2, mutation_scale=30),
                        xycoords='data', textcoords='data')

        # Peak value labels
        if is_Peak_label:
            nominal_positions = [1350, 1580, 2700]
            if not is_2D_mark: nominal_positions = [1350, 1580]
            search_tol = 40

            for idx_spectrum, (y_shift, y_mask) in enumerate(zip(y_shifted, y_masked)):
                for pos_nom in nominal_positions:
                    mask_win = (x_masked >= pos_nom - search_tol) & (x_masked <= pos_nom + search_tol)
                    if np.any(mask_win):
                        x_win = x_masked[mask_win]
                        y_win = np.array(y_mask)[mask_win]
                        prom = max(y_win.max() * 0.05, 1e-12)
                        peaks_rel, props = find_peaks(y_win, prominence=prom)
                        if len(peaks_rel) > 0:
                            best_idx = peaks_rel[np.argmax(props["prominences"])]
                            peak_x = float(x_win[best_idx])
                            peak_y_unshifted = float(y_win[best_idx])
                        else:
                            best_idx = int(np.argmax(y_win))
                            peak_x = float(x_win[best_idx])
                            peak_y_unshifted = float(y_win[best_idx])
                    else:
                        gidx = int(np.argmin(np.abs(x_masked - pos_nom)))
                        peak_x = float(x_masked[gidx])
                        peak_y_unshifted = float(y_mask[gidx])

                    peak_y_display = float(peak_y_unshifted + shifts[idx_spectrum])

                    if peak_label_style.lower() == "horizontal":
                        text_str = f"{peak_x:.0f}"
                    elif peak_label_style.lower() == "vertical":
                        text_str = "\n".join(list(f"{int(peak_x)}"))

                    ax.text(peak_x, peak_y_display, text_str,
                            ha="center", va="bottom", fontsize=18, fontweight='bold')

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.4, transparent=True, facecolor='white')

        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = RamanPlotterGUI(root)
    root.mainloop()
