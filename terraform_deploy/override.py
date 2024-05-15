import sys
import json

if __name__ == '__main__':

    data = {'module': {'tig': {'source': sys.argv[1], 'lambda_container_image_uri': sys.argv[2]}}}
    with open('override.tf.json', 'w') as f:
        json.dump(data, f)