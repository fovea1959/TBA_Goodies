import argparse
import json
import logging
import sys

import matplotlib as mpl

import matplotlib.pyplot as plt
import numpy as np

import tba_cache


def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", help="event key", required=True)
    parser.add_argument("--offline", action='store_true', help="don't go to internet")
    parser.add_argument("--lazy", action='store_true', help="only go to internet if not in cache")
    args = parser.parse_args(argv)

    logging.info ("invoked with %s", args)

    with tba_cache.TBACache(offline=args.offline, lazy=args.lazy) as tba:
        matches = tba.get_matches_for_event(event_key=args.event)
        all_scores = {}
        for match in matches:
            if match['comp_level'] == 'qm':
                scores = []
                for color in ('blue', 'red'):
                    score = match['score_breakdown'][color]['totalPoints']
                    scores.append(score)
                all_scores[match['key']] = scores

    # print(json.dumps(all_scores, indent=1))

    x = []
    y = []
    x_max = 0
    y_max = 0
    for i, scores in enumerate(all_scores.values()):
        xv = scores[0] + scores[1]
        yv = abs(scores[0] - scores[1])
        x.append(xv)
        y.append(yv)
        x_max = max(x_max, xv)
        y_max = max(y_max, yv)
        print(xv, ',', yv)


    print('x_max', x_max)
    print('y_max', y_max)
    x_binsize = 100
    y_binsize = 100
    x_max = (int(x_max/x_binsize) + 1) * x_binsize
    y_max = (int(y_max/y_binsize) + 1) * y_binsize
    print('x_max', x_max)
    print('y_max', y_max)
    x_edges = list(range(0, x_max+1, x_binsize))
    y_edges = list(range(0, y_max+1, y_binsize))
    print('x_edges', x_edges)
    print('y_edges', y_edges)
    heatmap, x_edges, y_edges = np.histogram2d(x, y, bins=(x_edges, y_edges))
    print(heatmap)
    print('x_edges', x_edges)
    print('y_edges', y_edges)

    mpl.rcParams["savefig.directory"] = "."
    mpl.rcParams["savefig.format"] = "pdf"

    if False:
        # 2. Create the heatmap (need to transpose)
        #plt.imshow(heatmap, cmap='viridis', extent=[0, x_edges[-2]-x_binsize, 0, y_edges[-2]-y_binsize], origin='lower', aspect='auto')  # Choose a colormap like 'viridis', 'hot', or 'magma'
        plt.imshow(heatmap, cmap='viridis', origin='lower', aspect='auto')  # Choose a colormap like 'viridis', 'hot', or 'magma'
        # 3. Add a colorbar legend
        plt.colorbar(label='Intensity Value')

        # 4. Add titles and labels
        plt.title(args.event)
        plt.xlabel("Total Score")
        plt.ylabel("Score Differential")

    plt.figure(f"{args.event} Scoring Scatter Plot")
    plt.title(f"{args.event} Scoring")
    plt.scatter(x, y)
    plt.xlabel("Total Score")
    plt.ylabel("Score Differential")
    plt.xticks(range(0, 701, 100))
    plt.yticks(range(0, 501, 100))

    plt.show()


if __name__ == '__main__':
    main(sys.argv[1:])
