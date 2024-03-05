from ragatouille import RAGPretrainedModel

RAG = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")

def main():

    amazon_tos_file = "data/amazontos.txt"
    amazon_tos = open(amazon_tos_file, "r").readlines()

    amazon_tos_str = "".join(line for line in amazon_tos)
    print(amazon_tos_str)

    print("before rag_index")

    RAG.index(
        collection=[amazon_tos_str], 
        document_ids=['amazon'],
        document_metadatas=[{"entity": "Terms of Services", "source": "Amazon"}],
        index_name="Amazon", 
        max_document_length=180, 
        split_documents=True
        )

if __name__ == "__main__":
    main()
