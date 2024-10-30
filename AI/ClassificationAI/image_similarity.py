# -*- coding: utf-8 -*-
import sys
import json
from PIL import Image
import imagehash
import os
import concurrent.futures

# �ؽ� ĳ�� �ʱ�ȭ
hash_cache = {}

def get_image_hash(image_path):
    if image_path in hash_cache:
        return hash_cache[image_path]
    else:
        image = Image.open(image_path).convert("L")  # ȸ������ ��ȯ
        # ��� �ؽÿ� pHash�� ���
        average_hash = imagehash.average_hash(image)
        perceptual_hash = imagehash.phash(image)
        hash_cache[image_path] = (average_hash, perceptual_hash)
        return average_hash, perceptual_hash

def resize_image(image, size=(128, 128)):
    # LANCZOS ���� ���
    return image.resize(size, Image.LANCZOS)

def compute_similarity(ref_path, input_hash):
    ref_image = Image.open(ref_path).convert("L")  # ȸ������ ��ȯ
    ref_hash = get_image_hash(ref_path)

    # �ؽ� �Ÿ� ��� (���缺)
    average_hash_difference = input_hash[0] - ref_hash[0]
    perceptual_hash_difference = input_hash[1] - ref_hash[1]
    
    # ��� �ؽÿ� pHash�� ������ ����Ͽ� ���絵 ���
    # ���̰��� Ŀ������ ������ ������
    similarity_score = max(0, 100 - (average_hash_difference * 10) - (perceptual_hash_difference * 5))

    # ���絵�� 0 ������ ��� 0���� ����
    if similarity_score < 0:
        similarity_score = 0

    return os.path.basename(ref_path), round(similarity_score, 1)  # �Ҽ��� �Ʒ� �� �ڸ����� �ݿø�

def find_similar_images(image_path, reference_images):
    input_image = resize_image(Image.open(image_path).convert("L"))  # ȸ������ ��ȯ �� ��������
    input_hash = get_image_hash(image_path)

    similar_images = []

    # ��Ƽ ���μ����� ����Ͽ� ���絵 ���
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_ref = {executor.submit(compute_similarity, ref_path, input_hash): ref_path for ref_path in reference_images}

        for future in concurrent.futures.as_completed(future_to_ref):
            ref_path = future_to_ref[future]
            try:
                ref_name, similarity_score = future.result()
                if similarity_score > 0:
                    similar_images.append({"similarImage": ref_name, "similarity": similarity_score})
            except Exception as e:
                # ���� �߻� �� �����ϰ� ���
                print("Error processing {}: {}".format(ref_path, str(e)))

    # ���絵�� ���� �̹��� ����
    similar_images.sort(key=lambda x: x["similarity"], reverse=True)

    # ���� ������ ���� 3�� �̹��� ��ȯ
    return similar_images[:3]

if __name__ == "__main__":
    input_image_path = sys.argv[1]
    reference_images_dir = "C:\\Users\\User1\\Documents\\GitHub\\Capstonesecond\\AI\\DB"
    reference_images = [os.path.join(reference_images_dir, img) for img in os.listdir(reference_images_dir) if img.endswith(('jpg', 'jpeg', 'png'))]

    # ���� ������ �̹��� ã��
    similar_images = find_similar_images(input_image_path, reference_images)

    # ��� JSON���� ���
    result = {
        "similarImages": similar_images
    }

    print(json.dumps(result, ensure_ascii=False))  # JSON ��� �� �����ڵ� ����
