Pydantic Model Generator command: 

```
PS D:\CourseMap\etl> python -m datamodel_code_generator `                                                                                                                           
>>   --input .\schemas\universal_course.json `                                                    
>>   --input-file-type jsonschema `
>>   --output .\core\models\course.py `
>>   --output-model-type pydantic_v2.BaseModel `
>>   --field-constraints
```