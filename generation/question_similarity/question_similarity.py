import json
from sentence_transformers import SentenceTransformer
from torch.nn.functional import cosine_similarity, normalize
from torch import argmax, stack, cat, cdist
import matplotlib.pyplot as plt
from tqdm import tqdm
import os


base_dir = (
    "../generated_data/satdb_from_spider_full_3x_simplified/question_similarity_check"
)
spider_fn = "masked_spider_train.json"
satdb_fn = "masked_all_satdb_train.json"
out_fn = "spider_most_similar_qs.json"
# TODO: match  n_qs most similar questions?
# num_qs = 3

model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device="mps")


def generate_embeddings(exs):
    texts = [ex["masked_question"] for ex in exs]
    # try with og question
    # texts = [ex["question"] for ex in examples]
    # print(len(texts))
    # print(texts)
    embeddings = model.encode(texts, convert_to_tensor=True, normalize_embeddings=True)
    return embeddings


def compute_similarity(spider_embeds, satdb_embeds):
    # spider = spider_embeds[:, None, :].expand(-1, len(satdb_embeds), -1)
    # satdb = satdb_embeds[None, :, :].expand(len(spider_embeds), -1, -1)
    # print(spider.shape)
    # print(satdb.shape)
    # TODO: make sure this is right?
    sim = normalize(spider_embeds, dim=-1) @ normalize(satdb_embeds, dim=-1).T
    # sim = cdist(spider_embeds, satdb_embeds)
    # sim = spider_embeds @ satdb_embeds.T
    # print(sim.shape)
    # sim = cosine_similarity(spider, satdb, dim=-1)
    return sim


if __name__ == "__main__":
    spider_data = json.load(open(os.path.join(base_dir, spider_fn), "r"))
    satdb_data = json.load(open(os.path.join(base_dir, satdb_fn), "r"))

    spider_data_by_db = {}
    for ex in spider_data:
        db_id = ex["db_id"]
        if db_id in spider_data_by_db:
            spider_data_by_db[db_id].append(ex)
        else:
            spider_data_by_db[db_id] = [ex]

    satdb_data_by_db = {}
    for ex in satdb_data:
        db_id = ex["db_id"]
        if db_id in satdb_data_by_db:
            satdb_data_by_db[db_id].append(ex)
        else:
            satdb_data_by_db[db_id] = [ex]

    spider_embeds_by_db = {
        db_id: generate_embeddings(db_data).cpu()
        for db_id, db_data in tqdm(spider_data_by_db.items())
    }
    # satdb_embeds = generate_embeddings(satdb_data).cpu()
    satdb_embeds_by_db = {
        db_id: generate_embeddings(db_data).cpu()
        for db_id, db_data in tqdm(satdb_data_by_db.items())
    }
    # print(spider_embeds.shape)
    # print(satdb_embeds.shape)

    # TODO: full matrices take too much memory
    sims_by_db = {}

    # for batch in tqdm(spider_embeds.chunk(100)):
    #     sims.append(compute_similarity(batch, satdb_embeds))
    # sim = cat(sims, dim=0)
    # print(sim.shape)

    for db_id, spider_batch in tqdm(spider_embeds_by_db.items()):
        satdb_batch = satdb_embeds_by_db[db_id]
        sims_by_db[db_id] = compute_similarity(spider_batch, satdb_batch)

    # TODO: find n most similar idxs
    # closest_idxs = argmax(sim, dim=-1)
    # print(closest_idxs.shape)

    # all_ex_sims = []

    # for i, ex in enumerate(spider_data):
    #     satdb_idx = closest_idxs[i]
    #     ex_sim = sim[i, satdb_idx].item()
    #     all_ex_sims.append(ex_sim)
    #     satdb_ex = satdb_data[satdb_idx]
    #     ex["satdb_comp"] = {"example": satdb_ex, "similarity": ex_sim}

    most_similar_exs = []

    for db_id, sim in tqdm(sims_by_db.items()):
        spider_exs = spider_data_by_db[db_id]
        satdb_exs = satdb_data_by_db[db_id]

        closest_idxs = argmax(sim, dim=-1)
        # print(closest_idxs.shape)

        all_ex_sims = []

        for i, ex in enumerate(spider_exs):
            satdb_idx = closest_idxs[i]
            ex_sim = sim[i, satdb_idx].item()
            all_ex_sims.append(ex_sim)
            satdb_ex = satdb_exs[satdb_idx]
            ex["satdb_comp"] = {"example": satdb_ex, "similarity": ex_sim}
            most_similar_exs.append(ex)

    # json.dump(spider_data, open(out_fn, "w"))
    json.dump(most_similar_exs, open(os.path.join(base_dir, out_fn), "w"))
    all_ex_sims = [ex["satdb_comp"]["similarity"] for ex in most_similar_exs]
    plt.hist(all_ex_sims)
    plt.show()
