"""
This file is part of Satyrn.
Satyrn is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version.
Satyrn is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with Satyrn.
If not, see <https://www.gnu.org/licenses/>.
"""

from typing import Dict, List

import os
import threading
import chromadb
import json
from uuid import uuid4
from chromadb.config import DEFAULT_DATABASE, DEFAULT_TENANT, Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# TODO: refactor this into env vars
DEVICE = "mps"

ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2", device=DEVICE)


def create_persistent_client(path):
    return chromadb.PersistentClient(
        path=path,
        settings=Settings(anonymized_telemetry=False),
        tenant=DEFAULT_TENANT,
        database=DEFAULT_DATABASE,
    )


class ExampleBank:
    _client_lock = threading.Lock()
    _clients_by_dir = {}

    def __init__(self, persist_dir=None):
        if persist_dir is None:
            satyrn_root_dir = os.getenv("SATYRN_ROOT_DIR")
            example_bank_path = os.getenv("QUESTION_REPHRASING_EXAMPLE_BANK_PATH")
            if not satyrn_root_dir or not example_bank_path:
                raise ValueError(
                    "SATYRN_ROOT_DIR and QUESTION_REPHRASING_EXAMPLE_BANK_PATH must be set "
                    "before initializing ExampleBank."
                )
            persist_dir = os.path.join(satyrn_root_dir, example_bank_path)

        query_dir = os.path.join(persist_dir, "queries")
        question_dir = os.path.join(persist_dir, "questions")
        os.makedirs(query_dir, exist_ok=True)
        os.makedirs(question_dir, exist_ok=True)

        try:
            cache_key = (query_dir, question_dir)
            with self._client_lock:
                if cache_key not in self._clients_by_dir:
                    self._clients_by_dir[cache_key] = (
                        create_persistent_client(query_dir),
                        create_persistent_client(question_dir),
                    )
                self.query_client, self.question_client = self._clients_by_dir[cache_key]
        except Exception as exc:
            raise RuntimeError(
                "Failed to initialize ExampleBank Chroma clients. "
                f"persist_dir={persist_dir!r}, "
                f"query_dir_exists={os.path.exists(query_dir)}, "
                f"question_dir_exists={os.path.exists(question_dir)}, "
                f"query_files={os.listdir(query_dir)[:5] if os.path.exists(query_dir) else []}, "
                f"question_files={os.listdir(question_dir)[:5] if os.path.exists(question_dir) else []}"
            ) from exc
        # TODO: maybe add a skeletonized client?

    def db_to_collection(self, db_id):
        # need to use this for third batch or prior or recreate those banks
        # return (rid + "-" + plan_type)[:63]
        return db_id[:63]

    def parse_and_store_example(self, exs, db_id, split):
        # ids = [str(uuid4()) for i in exs]
        queries = exs["queries"]
        questions = exs["questions"]
        ids = [str(uuid4()) for i in queries]
        question_metadatas = [{"query": q, "db_id": db_id, "split": split} for q in queries]
        query_metadatas = [{"question": q, "db_id": db_id, "split": split} for q in questions]

        # add query embedding to collection for specific db
        collection = self.query_client.get_or_create_collection(
            name=self.db_to_collection(db_id),
            embedding_function=ef,
        )
        collection.add(
            # ids=[str(uuid4())],
            # documents=[query],
            # metadatas={"question": question, "db_id": db_id, "split": split},
            ids = ids,
            documents=queries,
            metadatas=query_metadatas
        )

        # add query embedding to collection for split
        collection = self.query_client.get_or_create_collection(
            name=self.db_to_collection(split),
            embedding_function=ef,
        )
        collection.add(
            ids = ids,
            documents=queries,
            metadatas=query_metadatas
        )

        # add question embedding to question_client collection for db
        collection = self.question_client.get_or_create_collection(
            # collection names have limited length
            name=self.db_to_collection(db_id),
            embedding_function=ef,
        )
        collection.add(
            # ids=[str(uuid4())],
            # documents=[question],
            # metadatas={
            #     "query": query,
            #     "db_id": db_id,
            #     "split": split,
            # },
            ids = ids,
            documents=questions,
            metadatas=question_metadatas,
        )

        # add question embedding to question_client collection for split
        collection = self.question_client.get_or_create_collection(
            name=self.db_to_collection(split),
            embedding_function=ef,
        )
        collection.add(
            ids = ids,
            documents=questions,
            metadatas=question_metadatas,
        )

    # need to call load examples to populate db for first time
    def load_examples(self, dir):
        for fn in os.listdir(dir):
            if fn not in ["test.json", "train.json", "dev.json"]:
                continue
            print(fn)
            data = json.load(open(os.path.join(dir, fn), "r"))
            
            # group examples by db then store all at once
            data_by_db_id = {}
            for ex in data:
                db_id = ex["db_id"]
                if db_id in data_by_db_id:
                    data_by_db_id[db_id]["questions"].append(ex["question"])
                    # for spider - use query key
                    # data_by_db_id[db_id]["queries"].append(ex["query"])
                    # for bird - use sql key
                    data_by_db_id[db_id]["queries"].append(ex["SQL"])
                else:
                    # # data_by_db_id[db_id] = {"questions": [ex["question"]], "queries": ex["queries"]}
                    # # for spider - use query key
                    # data_by_db_id[db_id] = {"questions": [ex["question"]], "queries": [ex["query"]]}
                    # for bird - use sql key
                    data_by_db_id[db_id] = {"questions": [ex["question"]], "queries": [ex["SQL"]]}
            
            for db_id, db_exs in data_by_db_id.items():
                # self.store_examples(db_exs, db_id, fn[:-5])
                self.parse_and_store_example(db_exs, db_id, fn[:-5])
                        

    # use this to return better plans based on intially generated plan
    def query_examples_for_query(self, rid, split, query, max_results=3):
        questions = []
        plans = []
        distances = []
        db_ids = []
        splits = []
        
        collection = self.query_client.get_collection(name=self.db_to_collection(split))
        split_results = collection.query(query_texts=[query], n_results=max_results)
        print(split_results)
        # print("COLLECTION:", collection.name)
        # print("DISTANCE:", result["distances"][0][0])
        # questions.append(result["metadatas"][0][0]["question"])
        # plans.append(json.loads(result["documents"][0][0]))
        # distances.append(result["distances"][0][0])
        # rings.append(result["metadatas"][0][0]["ring_id"])
        # only return the most similar results
        # results_by_ring = {}
        # n = 0
        # for q, p, r, _ in sorted(
        #     zip(questions, plans, rings, distances), key=lambda x: x[-1]
        # ):
        #     if n >= max_results:
        #         break
        #     n += 1
        #     if r in results_by_ring.keys():
        #         results_by_ring[r].append(tuple((q, p)))
        #     else:
        #         results_by_ring[r] = [tuple((q, p))]
        # # return the results grouped by ring id for improved prompt
        # return results_by_ring

    # use this for first generation attempt
    def query_examples_for_question(
        self, rid, question, max_results=3,
    ):
        questions = []
        queries = []
        distances = []
        dbs = []
        for collection in self.question_client.list_collections():
            if rid[:63] in collection.name:
                # print(collection.name)
                results = collection.query(query_texts=[question], n_results=max_results)
                # print(result)
                # print("COLLECTION:", collection.name)
                # print("DISTANCE:", result["distances"][0][0])
                for r in results:
                    print(r)
                    # queries.append(json.loads(result["metadatas"][0][0]["plan"]))
                    # questions.append(result["documents"][0][0])
                    # distances.append(result["distances"][0][0])
                    # dbs.append(result["metadatas"][0][0]["ring_id"])
          # only return the most similar results
        # results_by_db = {}
        # n = 0
        # for q, p, r, _ in sorted(
        #     zip(questions, queries, dbs, distances), key=lambda x: x[-1]
        # ):
        #     if n >= max_results:
        #         break
        #     n += 1
        #     if r in results_by_ring.keys():
        #         results_by_ring[r].append(tuple((q, p)))
        #     else:
        #         results_by_ring[r] = [tuple((q, p))]
        # # return the results grouped by ring id for improved prompt
        # return results_by_ring


    # use this to return better plans based on intially generated plan
    def query_examples(self, db_id, split, query, question, max_results=3):
        # return 1 example based on each of
        #   - question similarity to others for the same db
        #   - query similarity to others for same db
        #   - query similarity to other queries in the same split
        #       - may want to update this to use some kind of skeleton

        # TODO: support batching

        questions = []
        queries = []
        # could use these later
        # distances = []
        # db_ids = []
        ids = []
        
        collection = self.query_client.get_collection(name=self.db_to_collection(split))
        split_query_results = collection.query(query_texts=[query], n_results=max_results)
        # print(split_query_results)

        collection = self.query_client.get_collection(name=self.db_to_collection(db_id))
        db_query_results = collection.query(query_texts=[query], n_results=max_results)
        # print(db_query_results)

        collection = self.question_client.get_collection(name=self.db_to_collection(db_id))
        db_question_results = collection.query(query_texts=[question], n_results=max_results)
        # print(db_question_results)

        # combine examples without duplicates
        # keys: ids, documents, metadatas:question or query and split and db_id
        # for now ignore db_id
        for ex_id, md, ex_query in zip(db_query_results["ids"][0], db_query_results["metadatas"][0], db_query_results["documents"][0]):
            if ex_id not in ids and md["split"] == split:
                questions.append(md["question"])
                queries.append(ex_query)
                break
            
        for ex_id, md, ex_question in zip(db_question_results["ids"][0], db_question_results["metadatas"][0], db_question_results["documents"][0]):
            if ex_id not in ids and md["split"] == split:
                questions.append(ex_question)
                queries.append(md["query"])
                break
            
        for ex_id, md, ex_query in zip(split_query_results["ids"][0], split_query_results["metadatas"][0], split_query_results["documents"][0]):
            if ex_id not in ids and md["split"] == split:
                questions.append(md["question"])
                queries.append(ex_query)
                break
        return {"queries": queries, "questions": questions}

            
