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

## SheetRM-10 Dataset
We release 10 representative tasks in our proposed SheetRM dataset, which is called SheetRM-10. We run the vision-enabled SheetAgent experiment using SheetRM-10. For details, please refer to Appendix F.2 in the paper.

In our commitment to advancing open research, we are pleased to announce the release of a portion of our dataset. We understand the importance of data accessibility and are diligently working to organize and maintain the remaining dataset. As soon as it is ready, we will make it publicly available. We strive to ensure the highest quality and usability of our data.

The SheetRM-10 dataset is stored in `./sheetrm_10`, where `tasks.xlsx` records the metadata of the 10 tasks, and the `spreadsheets` folder stores the spreadsheet files. You can try these challenging tasks following the guidence of "Quick Start".

## Other Datasets
Our experiments involves other datasets, including:
- SheetCopilot Benchmark: https://github.com/BraveGroup/SheetCopilot
- WikiTableQuestions: https://github.com/ppasupat/WikiTableQuestions
- TabFact: https://github.com/wenhuchen/Table-Fact-Checking 
- FeTaQA: https://github.com/Yale-LILY/FeTaQA

You can download them via the links and test SheetAgent on the dataset you prefer. We provide impelmentation details of SheetAgent on these datasets (See Section Implementation Details).