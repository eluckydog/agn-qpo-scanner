"""
AGN QPO Analysis Pipeline

Methods:
1. Hilbert instantaneous phase φ(t)
2. Phase coherence (Rayleigh test, Kuiper test)
3. Lomb-Scargle periodogram (traditional baseline)
4. Wavelet power spectrum (time-frequency)
5. MC significance estimation
6. U(1) phase offset fit (von Mises)
"""
import numpy as np
from scipy import signal, optimize, stats


# ──────────────────────────────────────────
# 1. Hilbert Phase
# ──────────────────────────────────────────
def hilbert_phase(t, y, detrend=True):
    """
    Compute instantaneous phase via Hilbert transform.
    
    Parameters
    ----------
    t : array
        Time values (MJD, JD, etc.)
    y : array
        Magnitude values (could be unevenly sampled)
    detrend : bool
        Remove linear trend before Hilbert
    
    Returns
    -------
    phases : array
        Instantaneous phase φ(t) in radians [-π, π]
    amplitude : array
        Instantaneous amplitude A(t)
    """
    if detrend:
        y = signal.detrend(y)
    
    # If unevenly sampled, interpolate to uniform grid first
    dt = np.median(np.diff(t))
    if dt == 0:
        dt = 1.0
    
    t_uniform = np.arange(t[0], t[-1], dt)
    y_uniform = np.interp(t_uniform, t, y)
    
    # Hilbert transform
    analytic = signal.hilbert(y_uniform)
    phases = np.angle(analytic)
    amplitude = np.abs(analytic)
    
    return t_uniform, phases, amplitude


def phase_coherence(phases):
    """
    Rayleigh test for phase uniformity.
    Strong clustering → potential QPO.
    
    Returns
    -------
    R : float
        Mean resultant length (0 = uniform, 1 = perfect cluster)
    z : float
        Rayleigh statistic = N * R²
    p : float
        p-value under uniformity null
    """
    N = len(phases)
    if N < 3:
        return 0.0, 0.0, 1.0
    
    complex_phases = np.exp(1j * phases)
    C = np.mean(np.cos(phases))
    S = np.mean(np.sin(phases))
    R = np.sqrt(C**2 + S**2)
    z = N * R**2
    p = np.exp(-z) * (1 + (2*z - z*z) / (4*N)) if N > 10 else np.exp(-z)
    
    return R, z, min(p, 1.0)


def kuiper_test(phases):
    """
    Kuiper test for uniformity on circle.
    More sensitive than Rayleigh for multi-modal distributions.
    
    Returns
    -------
    V : float
        Kuiper statistic
    p : float
        p-value
    """
    from scipy.stats import kuiper
    # kuiper expects sorted values in [0,1]
    sorted_phases = np.mod(phases, 2*np.pi) / (2*np.pi)
    sorted_phases.sort()
    return kuiper(sorted_phases)


# ──────────────────────────────────────────
# 2. Lomb-Scargle Periodogram
# ──────────────────────────────────────────
def lomb_scargle(t, y, dy=None, min_period=1, max_period=None):
    """
    Compute Lomb-Scargle periodogram.
    
    Returns
    -------
    periods : array
        Trial periods (days)
    power : array
        Normalized power at each period
    best_period : float
        Period with maximum power
    best_power : float
        Maximum power value
    """
    if len(t) < 5:
        return np.array([]), np.array([]), 0.0, 0.0
    
    # Determine frequency range
    baseline = t[-1] - t[0]
    if max_period is None:
        max_period = baseline / 2
    if max_period < min_period:
        max_period = min_period * 2
    
    # Frequency resolution: scale with baseline; limit for speed on large datasets
    n_freq = int(baseline / min_period * 3)
    n_freq = min(max(n_freq, 30), 3000)
    
    min_freq = 1.0 / max_period
    max_freq = 1.0 / min_period
    freqs = np.linspace(min_freq, max_freq, n_freq)
    
    if dy is None:
        freq_power = signal.lombscargle(t, y, freqs)
    else:
        freq_power = signal.lombscargle(t, y, freqs, weights=1.0/dy**2)
    
    power = freq_power
    periods = 1.0 / freqs
    
    best_idx = np.argmax(power)
    best_period = periods[best_idx]
    best_power = power[best_idx]
    
    return periods, power, best_period, best_power


# ──────────────────────────────────────────
# 3. Wavelet (Time-Frequency)
# ──────────────────────────────────────────
def wavelet_spectrum(t, y, min_period=1, max_period=None, n_scales=100):
    """
    Morlet wavelet time-frequency analysis.
    
    Returns
    -------
    periods : array
        Period scales
    power : 2D array
        Power as function of (time, period)
    """
    if len(t) < 10:
        return None, None, None, None
    
    baseline = t[-1] - t[0]
    if max_period is None:
        max_period = baseline / 2
    
    dt = np.median(np.diff(t))
    if dt == 0:
        dt = 1.0
    
    # Uniformly sample
    t_uniform = np.arange(t[0], t[-1], dt)
    y_uniform = np.interp(t_uniform, t, y)
    
    # Remove linear trend
    y_uniform = signal.detrend(y_uniform)
    
    # Compute scales (periods)
    scales = np.logspace(np.log10(min_period), np.log10(max_period), n_scales)
    
    # CWT
    scales_cwt = scales / dt  # convert period to scale
    coefs = signal.cwt(y_uniform, signal.morlet2, scales_cwt, w=5)
    power = np.abs(coefs)**2
    
    return t_uniform, scales, power, np.sum(power, axis=1)  # average power per scale


# ──────────────────────────────────────────
# 4. Significance via MC
# ──────────────────────────────────────────
def mc_significance_ls(t, y, n_sim=500, min_period=1, max_period=None):
    # Adaptive: reduce sims for large datasets where LS is expensive
    if len(t) > 500:
        n_sim = min(n_sim, 200)
    elif len(t) > 200:
        n_sim = min(n_sim, 300)
    """
    Monte Carlo significance of LS peak against red-noise null.
    Shuffle the time stamps to preserve flux distribution.
    """
    baseline = t[-1] - t[0]
    if max_period is None:
        max_period = baseline / 2
    
    # Observed LS
    periods, power, best_period, best_power = lomb_scargle(t, y, min_period=min_period, max_period=max_period)
    
    if len(power) == 0:
        return 1.0, 0.0
    
    # MC null distribution
    null_powers = []
    for _ in range(n_sim):
        y_shuffled = np.random.permutation(y)
        _, _, _, p_best = lomb_scargle(t, y_shuffled, min_period=min_period, max_period=max_period)
        null_powers.append(p_best)
    
    null_powers = np.sort(null_powers)
    threshold_95 = null_powers[int(0.95 * n_sim)]
    threshold_99 = null_powers[int(0.99 * n_sim)]
    
    # p-value: fraction of null samples with power ≥ observed
    p_value = np.mean(np.array(null_powers) >= best_power)
    
    return p_value, best_power, best_period, threshold_95, threshold_99


# ──────────────────────────────────────────
# 5. U(1) von Mises Fit
# ──────────────────────────────────────────
def von_mises_pdf(phi, mu, kappa):
    """von Mises PDF (unnormalized)."""
    return np.exp(kappa * np.cos(phi - mu))


def fit_von_mises(phases, bins=36):
    """
    Fit von Mises distribution to folded phases.
    
    Returns
    -------
    mu : float
        Mean direction (peak phase)
    kappa : float
        Concentration
    r_squared : float
        Goodness of fit
    """
    if len(phases) < 10:
        return 0.0, 0.0, 0.0
    
    # Histogram
    hist, bin_edges = np.histogram(np.mod(phases, 2*np.pi), bins=bins, range=(0, 2*np.pi), density=True)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # Fit von Mises
    def neg_log_likelihood(params):
        mu, kappa = params
        if kappa < 0:
            return 1e10
        model = von_mises_pdf(bin_centers, mu, kappa)
        model = model / (np.mean(model) * 2 * np.pi)
        return -np.sum(hist * np.log(model + 1e-10))  # cross-entropy
    
    result = optimize.minimize(neg_log_likelihood, [np.pi, 1.0], method='L-BFGS-B',
                               bounds=[(0, 2*np.pi), (0.01, 50)])
    mu_fit, kappa_fit = result.x
    
    # R²
    model_fit = von_mises_pdf(bin_centers, mu_fit, kappa_fit)
    model_fit = model_fit / (np.mean(model_fit) * 2 * np.pi)
    ss_res = np.sum((hist - model_fit)**2)
    ss_tot = np.sum((hist - np.mean(hist))**2)
    r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    
    return mu_fit, kappa_fit, r_sq


# ──────────────────────────────────────────
# 6. Complete Pipeline
# ──────────────────────────────────────────
def analyze_light_curve(t, y, target_period=None, mc_sims=200):
    """
    Full QPO analysis pipeline.
    
    Parameters
    ----------
    t : array
        Time values (days, MJD format)
    y : array
        Magnitude values
    target_period : float or None
        Expected period for phase folding (if known)
    mc_sims : int
        Monte Carlo simulations for significance
    
    Returns
    -------
    dict with all analysis results
    """
    results = {}
    
    # Remove NaN/Inf
    mask = np.isfinite(t) & np.isfinite(y)
    t, y = t[mask], y[mask]
    
    if len(t) < 5:
        return {"error": "too few points"}
    
    # 1. Lomb-Scargle
    periods, power, best_period, best_power = lomb_scargle(t, y)
    results["ls_period"] = float(best_period)
    results["ls_power"] = float(best_power)
    results["ls_periods"] = periods.tolist()[:500]
    results["ls_power_curve"] = power.tolist()[:500]
    
    # 2. MC significance
    p_val, obs_power, top_period, thresh_95, thresh_99 = mc_significance_ls(t, y, n_sim=mc_sims)
    results["mc_p_value"] = float(p_val)
    results["mc_threshold_95"] = float(thresh_95)
    results["mc_threshold_99"] = float(thresh_99)
    results["significant_95"] = bool(obs_power >= thresh_95)
    results["significant_99"] = bool(obs_power >= thresh_99)
    
    # 3. Phase folding (at best period)
    phase_best = np.mod(t / top_period, 1.0) * 2*np.pi
    R, z, phase_p = phase_coherence(phase_best)
    results["phase_rayleigh_R"] = float(R)
    results["phase_rayleigh_z"] = float(z)
    results["phase_rayleigh_p"] = float(phase_p)
    
    # 4. Phase folding at target period (if given)
    if target_period:
        phase_target = np.mod(t / target_period, 1.0) * 2*np.pi
        R_t, z_t, p_t = phase_coherence(phase_target)
        results["target_rayleigh_R"] = float(R_t)
        results["target_rayleigh_z"] = float(z_t)
        results["target_rayleigh_p"] = float(p_t)
        results["target_period"] = float(target_period)
    
    # 5. von Mises fit to folded phases
    mu, kappa, r2 = fit_von_mises(phase_best)
    results["vm_mu"] = float(mu)
    results["vm_kappa"] = float(kappa)
    results["vm_r_squared"] = float(r2)
    
    # Summary
    if phase_p < 0.01:
        results["verdict"] = "QPO CANDIDATE"
        results["confidence"] = "high" if phase_p < 0.001 else "moderate"
    elif phase_p < 0.05:
        results["verdict"] = "MARGINAL"
        results["confidence"] = "low"
    else:
        results["verdict"] = "NO SIGNAL"
        results["confidence"] = None
    
    return results
