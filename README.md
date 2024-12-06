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

## SheetRM Dataset
We have released approximately 60% of the data from the proposed SheetRM dataset (including 25 spreadsheets and 180 tasks).

As part of our commitment to open research, we are excited to announce the release of a portion of our dataset. We understand the importance of data accessibility and are actively working on organizing and maintaining the remaining dataset to avoid further privacy or other issues. Once ready, we will make it available to the public. We strive to ensure the highest quality and usability of our data.

These data are stored in `./sheetrm`, with `tasks.xlsx` containing the metadata for the 180 tasks. The spreadsheets are stored in the `spreadsheets` directory. You can try these challenging tasks under the guidance of "Quick Start".


## Other Datasets
Our experiments involves other datasets, including:
- SheetCopilot Benchmark: https://github.com/BraveGroup/SheetCopilot
- WikiTableQuestions: https://github.com/ppasupat/WikiTableQuestions
- TabFact: https://github.com/wenhuchen/Table-Fact-Checking 
- FeTaQA: https://github.com/Yale-LILY/FeTaQA

You can download them via the links and test SheetAgent on the dataset you prefer. We provide impelmentation details of SheetAgent on these datasets (See Section Implementation Details).
