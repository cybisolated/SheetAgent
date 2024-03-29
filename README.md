## Quick Start
Following the below steps to run SheetAgent:
1. Write your api_key and base_url in `openai.yaml`
2. Assign `workbook_path` and `instruction` args. Run the following command line.
```sh
python main.py --workbook_path "example_sheets/BoomerangSales.xlsx" \
--instruction "Count the number of each Product and put the results in a new sheet." \
--output_dir "./output" \ 
--few_shot_planner --verbose
```
3. The processed workbook named `workbook_new` will present in `output_dir`.

More arguments can be appended. Please refer to `main.py`.

We have provided sevral example spreadsheets in `example_sheets`. You can try your own task instruction at will.

The `milvus.yaml` file should be completed if you want to use the Retriever module. Besides, Milvus should be installed first (refer to https://github.com/milvus-io/milvus for detailed instructions).