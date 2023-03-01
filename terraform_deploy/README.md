# How to test TIG in AWS

* Step Function: TIG can be tested through the step funtion page, go to the step function of tig and click new execution, a execution id 
  will be created and needs to be put into the input message.
  
* Lambda : TIG can be tested through the lambda page on the AWS console by going to the test input for the lambda. Going through the lambda
  we need to have a previous execution id of step function.

## Setup

### Granule

* Put granule to test in protected bucket

## Message

We can input a message through the step function or through the lambda test input. TIG requires a step function execution id in the message.

### Setup Message

* execution_name: replace with new exectution id, by clicking new execution in step function page
* state_machine: arn of step function
* meta.buckets: replace all bucket names with ones you deployed
* collection: replace with collection info of the collection you're testing with info can be found at https://github.jpl.nasa.gov/podaac/cumulus-configurations
* payload: replace granule info with granule you wish to test

### Step Function Example Message

```
{
   "cumulus_meta":{
      "execution_name":"b8223356-ae4b-2586-a37b-5dd992f1f4fc",
      "message_source":"sfn",
      "state_machine":"arn:aws:states:us-west-2:206226843404:stateMachine:MyStateMachine"
   },
   "meta":{
      "buckets":{
         "internal":{
            "name":"sit-tig-internal",
            "type":"internal"
         },
         "private":{
            "name":"sit-tig-private",
            "type":"private"
         },
         "protected":{
            "name":"sit-tig-protected",
            "type":"protected"
         },
         "public":{
            "name":"sit-tig-public",
            "type":"public"
         }
      },
      "collection":{
         "dataType":"MODIS_T-JPL-L2P-v2019.0",
         "files":[
            {
               "bucket":"protected",
               "regex":"^.*\\.nc$",
               "sampleFileName":"20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_T-D-v02.0-fv01.0.nc",
               "type":"data"
            }
         ],
         "granuleId":"^([0-9]{14})-JPL-L2P_GHRSST-SSTskin-MODIS_T-[DN]-v02.0-fv01.0$",
         "granuleIdExtraction":"^(([0-9]{14})-JPL-L2P_GHRSST-SSTskin-MODIS_T-[DN]-v02.0-fv01.0)((\\.nc)|(\\.nc\\.md5)|(\\.cmr\\.json))?$",
         "name":"MODIS_T-JPL-L2P-v2019.0"
      }
   },
   "payload":{
      "granules":[
         {
            "granuleId":"20141010064000-JPL-L2P_GHRSST-SSTskin-MODIS_T-N-v02.0-fv01.0",
            "dataType":"MODIS_T-JPL-L2P-v2019.0",
            "files":[
               {
                  "bucket":"sit-tig-protected",
                  "fileName":"20141010064000-JPL-L2P_GHRSST-SSTskin-MODIS_T-N-v02.0-fv01.0.nc",
                  "type":"data",
                  "key":"MODIS_T-JPL-L2P-v2019.0/20141010064000-JPL-L2P_GHRSST-SSTskin-MODIS_T-N-v02.0-fv01.0.nc"
               }
            ]
         }
      ]
   }
}
```


### Lambda Example Message

```
{
   "cma":{
      "task_config":{
         "collection":"{$.meta.collection}",
         "cumulus_message":{
            "input":"{$.payload}",
            "outputs":[
               {
                  "source":"{$.input.granules}",
                  "destination":"{$.payload.granules}"
               }
            ]
         }
      },
      "event":{
         "cumulus_meta":{
            "cumulus_version":"9.9.0",
            "execution_name":"79254339-c7a4-ee08-d380-d72ae87a01fa",
            "message_source":"sfn",
            "state_machine":"arn:aws:states:us-west-2:206226843404:stateMachine:MyStateMachine",
            "workflow_start_time":1642706426362
         },
         "meta":{
            "buckets":{
               "internal":{
                  "name":"sit-tig-internal",
                  "type":"internal"
               },
               "private":{
                  "name":"sit-tig-private",
                  "type":"private"
               },
               "protected":{
                  "name":"sit-tig-protected",
                  "type":"protected"
               },
               "public":{
                  "name":"sit-tig-public",
                  "type":"public"
               }
            },
            "collection":{
               "dataType":"MODIS_T-JPL-L2P-v2019.0",
               "files":[
                  {
                     "bucket":"protected",
                     "regex":"^.*\\.nc$",
                     "sampleFileName":"20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_T-D-v02.0-fv01.0.nc",
                     "type":"data"
                  }
               ],
               "granuleId":"^([0-9]{14})-JPL-L2P_GHRSST-SSTskin-MODIS_T-[DN]-v02.0-fv01.0$",
               "granuleIdExtraction":"^(([0-9]{14})-JPL-L2P_GHRSST-SSTskin-MODIS_T-[DN]-v02.0-fv01.0)((\\.nc)|(\\.nc\\.md5)|(\\.cmr\\.json))?$",
               "name":"MODIS_T-JPL-L2P-v2019.0"
            }
         },
         "payload":{
            "granules":[
               {
                  "granuleId":"20141010064000-JPL-L2P_GHRSST-SSTskin-MODIS_T-N-v02.0-fv01.0",
                  "dataType":"MODIS_T-JPL-L2P-v2019.0",
                  "files":[
                     {
                        "bucket":"sit-tig-protected",
                        "fileName":"20141010064000-JPL-L2P_GHRSST-SSTskin-MODIS_T-N-v02.0-fv01.0.nc",
                        "type":"data",
                        "key":"MODIS_T-JPL-L2P-v2019.0/20141010064000-JPL-L2P_GHRSST-SSTskin-MODIS_T-N-v02.0-fv01.0.nc"
                     }
                  ]
               }
            ]
         }
      }
   }
}


```