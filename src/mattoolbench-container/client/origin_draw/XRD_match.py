import originpro as op
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.legend import Legend
from scipy.signal import find_peaks

# ====================== User Settings ======================
sample_sheets = ['WRTZSX5', 'WRTZSX6','WRTZSX7']
pdf_sheets    = ['PDF990073', 'PDF990030']
sample_labels = ['WRTZSX5', 'WRTZSX6','WRTZSX7']
pdf_labels    = ['PDF#99-0073', 'PDF#99-0030']

colors_sample = ['#EF0000', '#FEC211','#FAD733']
colors_pdf    = ['#1A6FDF', '#37AD6B']

save_path = r'..\output_result\XRD_final.png'
is_hkl = True
is_sample_legend= True
is_pdf_legend= True
#=========== Parameter Settings ========================
pdf_height_ratio = 0.40
gap_ratio = 0.28
pdf_gap_from_sample = 0.5           # slightly reduce gap for compact layout
annotate_hkl_on_samples = True
search_window = 0.4                 # Key! Match tolerance tightened to 0.4°
min_peak_height_ratio = 0.38        # mark major peaks only
min_peak_distance_deg = 1.8         # minimum peak spacing
# =======================================================

# 1. Read sample data
samples = []
for name in sample_sheets:
    wks = op.find_sheet('w', name)
    df = wks.to_df()
    x = df.iloc[:, 0].values
    y = df.iloc[:, 1].values
    samples.append((x, y))

# 2. Read PDF (for bar drawing and hkl matching)
pdf_data = []  # used for bar drawing
standard_peaks = []  # standard peaks for hkl matching

for idx, name in enumerate(pdf_sheets):
    wks = op.find_sheet('w', name)
    df = wks.to_df()
    x_pdf = df.iloc[:, 0].values.astype(float)
    inten = df.iloc[:, 1].values.astype(float)

    # —— Extract hkl ——
    data_part = df.iloc[:, 4:] if df.shape[1] > 4 else df.iloc[:, 2:]
    values = data_part.values.astype(str)
    hkl_list = []
    for row in values:
        items = [str(x).strip() for x in row if str(x).strip() not in ['nan','','<undefined>','None']]
        digits = []
        import re
        for item in items:
            m = re.search(r'-?\d+', item)
            if m: digits.append(m.group())
            if len(digits) >= 3: break
        if len(digits) == 3:
            hkl_list.append(f"({digits[0]}{digits[1]}{digits[2]})")
        else:
            hkl_list.append("")
    hkl_arr = np.array(hkl_list)

    # Save for bar drawing
    pdf_data.append((x_pdf, inten, hkl_arr))

    # Save for matching (normalized intensity)
    inten_norm = inten / inten.max() if inten.max() > 0 else inten
    standard_peaks.append(list(zip(x_pdf, hkl_arr, inten_norm)))

# 3. Display range
all_x = np.concatenate([x for x, y in samples])
xmin = max(10, np.percentile(all_x, 3))
xmax = min(90, np.percentile(all_x, 85))
# 4. Calculate offsets
def calculate_offsets(y_list, gap_ratio=0.28):
    maxima = [np.max(y) for y in y_list]
    minima = [np.min(y) for y in y_list]
    offsets = [0.0]
    current_top = maxima[0]
    for i in range(1, len(y_list)):
        shift = current_top - minima[i] + maxima[0] * gap_ratio
        offsets.append(shift)
        current_top = maxima[i] + shift
    return offsets, maxima[0]

y_only = [y for _, y in samples]
offsets_sample, base_height = calculate_offsets(y_only, gap_ratio)
y_shifted = [y + off for y, off in zip(y_only, offsets_sample)]
lowest_sample_y = min([arr.min() for arr in y_shifted])
highest_sample_y = max([arr.max() for arr in y_shifted])

# ==================== Plot ====================
plt.rcParams['font.family'] = 'Times New Roman'
fig, ax = plt.subplots(figsize=(10, 8))

# 1. Draw sample curves
lines = []
for i, ((x, y), offset, label) in enumerate(zip(samples, offsets_sample, sample_labels)):
    line, = ax.plot(x, y + offset, color=colors_sample[i], linewidth=0.5, label=label)
    lines.append(line)

# 2. Annotate hkl on sample peaks
if is_hkl and standard_peaks:
    search_window = 0.4
    min_peak_height_ratio = 0.35
    min_distance_deg = 1.8

    # Merge all reference peaks, sorted by intensity
    all_ref_peaks = []
    for peaks_list in standard_peaks:
        for pos, hkl, inten in peaks_list:
            if inten > 0.15:
                all_ref_peaks.append((pos, hkl, inten))
    all_ref_peaks.sort(key=lambda x: x[2], reverse=True)

    for i, ((x_sam, y_sam), offset, color) in enumerate(zip(samples, offsets_sample, colors_sample)):
        y_shifted_one = y_sam + offset

        # Find peaks independently for each sample
        peaks, _ = find_peaks(y_shifted_one,
                              height=np.max(y_shifted_one) * min_peak_height_ratio,
                              distance=len(x_sam) * min_distance_deg / (xmax - xmin),
                              prominence=np.max(y_shifted_one) * 0.12)

        # Prevent duplicate labels within each sample (allow same hkl across different samples)
        labeled_in_this_sample = set()

        for peak_idx in peaks:
            pos = x_sam[peak_idx]
            if not (xmin <= pos <= xmax):
                continue
            if round(pos, 1) in labeled_in_this_sample:  # prevent duplicates within this sample only
                continue

            best_hkl = None
            best_dist = float('inf')
            for ref_pos, hkl, _ in all_ref_peaks:
                dist = abs(pos - ref_pos)
                if dist < search_window and dist < best_dist:
                    best_dist = dist
                    best_hkl = hkl

            if best_hkl and best_hkl != "":
                ax.text(pos, y_shifted_one[peak_idx] + base_height * 0.10,
                        best_hkl,
                        ha='center', va='bottom',
                        fontsize=12, fontweight='bold',
                        color=color)
                labeled_in_this_sample.add(round(pos, 1))

# 3. Draw PDF bars
if pdf_data:
    pdf_h = base_height * pdf_height_ratio
    start_y = lowest_sample_y - base_height * pdf_gap_from_sample

    for idx, (x_pdf, inten, hkl) in enumerate(pdf_data):
        if inten.max() == 0: continue
        scaled = inten / inten.max() * pdf_h
        bottom = start_y - idx * (pdf_h + base_height * 0.18)

        mask = (x_pdf >= xmin-1) & (x_pdf <= xmax+1)
        ax.bar(x_pdf[mask], scaled[mask], bottom=bottom, width=0.11,
               color=colors_pdf[idx], alpha=0.92, align='center', label=pdf_labels[idx])

        if idx == len(pdf_data)-1:
            actual_pdf_bottom = bottom

# ==================== Aesthetics ====================
ax.set_xlim(xmin, xmax)
ax.set_xlabel(r'2\theta (°)', fontsize=22, fontweight='bold', labelpad=12)
ax.set_ylabel('Intensity (a.u.)', fontsize=22, fontweight='bold', labelpad=18)

step = 10 if (xmax-xmin)<=60 else 20
ax.set_xticks(np.arange(np.ceil(xmin/step)*step, xmax+step, step))
ax.tick_params(axis='both', labelsize=18, length=8, width=1.5)

for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_linewidth(1.5)
ax.set_yticks([])

# Right-side labels
total_ymin = start_y - len(pdf_data)*(pdf_h + base_height*0.18) - pdf_h if pdf_data else lowest_sample_y - base_height
total_ymax = highest_sample_y + base_height * 0.4
y_range = total_ymax - total_ymin

sample_patches = [plt.Line2D([0], [0], color=colors_sample[i], lw=4) for i in range(len(sample_labels))]

# First row: sample labels — placed at top
if is_sample_legend:
    sample_patches = [plt.Line2D([0], [0], color=colors_sample[i], lw=4)
                      for i in range(len(sample_labels))]

    leg1 = ax.legend(sample_patches, sample_labels,
                     loc='upper center',
                     bbox_to_anchor=(0.5, 0.96),   # slightly higher to leave space
                     ncol=len(sample_labels),
                     fontsize=16,
                     frameon=False,
                     columnspacing=2,
                     handlelength=1.8,
                     borderaxespad=0)

    ax.add_artist(leg1)

if pdf_data and is_pdf_legend:
    pdf_patches = [plt.Line2D([0], [0], color=colors_pdf[i], lw=8)
                   for i in range(len(pdf_data))]

    leg2 = ax.legend(pdf_patches, pdf_labels,
                     loc='upper center',
                     bbox_to_anchor=(0.5, 0.94),
                     ncol=len(pdf_data),
                     fontsize=15,
                     frameon=False,
                     columnspacing=2,
                     handlelength=2)


# —— Replace the original total_ymin calculation ——
if pdf_data:
    total_ymin = actual_pdf_bottom - base_height * 0.15   # Key fix! Minimal bottom margin
else:
    total_ymin = lowest_sample_y - base_height * 0.4

total_ymax = highest_sample_y + base_height * 0.8
ax.set_ylim(total_ymin, total_ymax)
plt.tight_layout(pad=1.8)
plt.savefig(save_path, dpi=600, bbox_inches='tight', facecolor='white')
print(f"XRD plot saved: {save_path}")
plt.show()
