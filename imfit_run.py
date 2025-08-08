from astropy.io import fits
import numpy as np
from astropy.table import Table
import astropy
import pandas as pd
import argparse
import sys
import os
from pathlib import Path
import pyimfit
import subprocess
import glob
IMAN_DIR = os.path.expanduser("~/Documents/iman_new")
sys.path.append(os.path.join(IMAN_DIR, 'decomposition/make_model'))
import make_model_ima_imfit


def run_imfit(args, band):
    # Assumes alread in directory
    #imfit -c config.dat image_g.fits --mask image_mask.fits --psf psf_patched_g.fits --noise image_g_invvar.fits --save-model g_model.fits --save-residual g_residual.fits --max-threads 4 --errors-are-weights
    # command = ["imfit", "-c", f"config_{band}.dat", f"image_{band}.fits", "--save-model", f"{band}_model.fits", "--save-residual", f"{band}_residual.fits", "--save-params", f"{band}_fit_params.txt", "--max-threads", f"{args.max_threads}"]
    command = ["imfit", "-c", f"{args.fit_type}_{band}.dat", f"image_{band}.fits", "--save-params", f"{args.fit_type}_{band}_fit_params.txt", "--max-threads", f"{args.max_threads}"]
    if args.mask or args.all:
        command.extend(["--mask", "image_mask.fits"])
    if args.psf or args.all:
        command.extend(["--psf", f"psf_patched_{band}.fits"])
    if args.invvar or args.all:
        command.extend(["--noise", f"image_{band}_invvar.fits", "--errors-are-weights"])
    if args.nm:
        # command.extend(["--nm", "--bootstrap 50", "--save-bootstrap", f"bootstrap_{band}.dat"])
        command.extend(["--nm"])
    if args.de:
        command.extend(["--de"])
    if args.de_lhs:
        command.extend(["--de_lhs"])
    
    p = subprocess.Popen(command)
    p.wait()

def main(args):
    if not(args.p == None):
        p = Path(args.p).resolve()
        os.chdir(p)

    if args.r:
        structure = os.walk(".")
        for root, dirs, files in structure:
            if not(files == []):
                # Assumes data is at the end of the file tree
                img_files = sorted(glob.glob(os.path.join(Path(root), "image_?.fits")))

                for img_file in img_files:
                        band = img_file[-6] # Yes I know this is not the best way
                        os.chdir(Path(root))
                        if not(any([f"{args.fit_type}_{band}_composed.fits" in files, f"{args.fit_type}_{band}_fit_params.txt" in files])) or args.overwrite:
                            # Assumes the names of the files for the most part
                            # config file should be called config_[band].dat, may also include a way to change that 
                            run_imfit(args, band)
                        os.chdir(p)
    else:
        img_files = sorted(glob.glob(os.path.join(Path("."), "image_?.fits")))

        for img_file in img_files:
                band = img_file[-6] # Yes I know this is not the best way
                files = os.listdir(".")
                if not(any([f"{args.fit_type}_{band}_composed.fits" in files, f"{args.fit_type}_{band}_fit_params.txt" in files])) or args.overwrite:
                    # Assumes the names of the files for the most part
                    # config file should be called config_[band].dat, may also include a way to change that 
                    run_imfit(args, band)
                    img_file = f"image_{band}.fits"
                    psf_file = f"psf_patched_{band}.fits"
                    params_file = f"{args.fit_type}_{band}_fit_params.txt"
                    mask_file = f"image_mask.fits"
                    if args.make_composed and (not(f"{args.fit_type}_{band}_composed.fits" in files) or args.overwrite):
                        if args.mask:
                            img_dat = fits.open(img_file)
                            img = img_dat[0].data
                            mask = fits.open(mask_file)[0].data
                            img = img * (1 - mask)
                            fits.writeto("masked.fits", data=img, header=img_dat[0].header)

                            make_model_ima_imfit.main("masked.fits", params_file, psf_file, composed_model_file=f"{args.fit_type}_{band}_composed.fits", comp_names=["Host", "Polar"])
                            os.remove("./masked.fits")
                        else:
                            make_model_ima_imfit.main(img_file, params_file, psf_file, composed_model_file=f"{args.fit_type}_{band}_composed.fits", comp_names=["Host", "Polar"])



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-p", help="Path to folder containing galaxies")
    parser.add_argument("-r", help="Recursively go into subfolders to find", action="store_true")
    parser.add_argument("--overwrite", help="Overwrites existing configs", action="store_true")
    parser.add_argument("--mask", help="Use mask image", action="store_true")
    parser.add_argument("--psf", help="Use psf image", action="store_true")
    parser.add_argument("--invvar", help="Use invvar map", action="store_true")
    parser.add_argument("--all", help="Use mask, psf, and invvar map", action="store_true")
    parser.add_argument("--nm", help="Use Nelder-Mead simplex solver (instead of Levenberg-Marquardt)", action="store_true")
    parser.add_argument("--de", help="Use differential evolution solver", action="store_true")
    parser.add_argument("--de_lhs", help="Use differential evolution solver (with Latin hypercube sampling)", action="store_true")
    parser.add_argument("--max_threads", help="Max number of threads to use for a fit", type=int, default=4)
    parser.add_argument("--fit_type", choices=["2_sersic", "1_sersic_1_gauss_ring", "3_sersic"], default="2_sersic")
    parser.add_argument("--make_composed", help="Make a composed image of the galaxy (includes image, model, and components)", action="store_true")
    # TODO: Add more arguments for IMFIT options

    args = parser.parse_args()

    main(args)