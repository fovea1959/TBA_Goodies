import json
import pickle

with open('tba_cache.json', 'r') as f:
    print('loading')
    d = json.load(f)
    print('loaded')

    with open('data.pickle', 'wb') as f:
        # Pickle the 'data' dictionary using the highest protocol available.
        print('pickling')
        pickle.dump(d, f, pickle.HIGHEST_PROTOCOL)
        print('pickled')

    with open('data.json', 'w') as f:
        # Pickle the 'data' dictionary using the highest protocol available.
        print('dumping')
        json.dump(d, f)
        print('dumped')

    with open('data2.json', 'w') as f:
        # Pickle the 'data' dictionary using the highest protocol available.
        print('dumping')
        json.dump(d, f, indent=1)
        print('dumped')
