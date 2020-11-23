#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import sys
import pathlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, date, time
import time
import copy
import math
import json
import re


# In[2]:


df = pd.read_csv("./data/Δημου_13_10__20_10.csv")

df_cleaned = df.drop(columns = ["Gateway", "#"])
registers = ["temperature" , "lid", "operational"]
default_registers = list(np.unique(df_cleaned["Register"]))

dict_of_registers_matches = dict.fromkeys(registers, "")
for def_reg in default_registers:
    if ("λειτουργία" in def_reg):
        dict_of_registers_matches["operational"] = def_reg
    elif ("καπάκι" in def_reg):
        dict_of_registers_matches["lid"] = def_reg
    else:
        dict_of_registers_matches["temperature"] = def_reg

new_dict = dict((v,k) for k,v in dict_of_registers_matches.items())
df_cleaned = df_cleaned.replace({"Register" : new_dict})
df_cleaned["Date"] = df_cleaned["Date"] + " " + df_cleaned["Time"]
df_cleaned = df_cleaned.drop(columns="Time")
df_cleaned['Date'] = (df_cleaned['Date'].apply(lambda x: time.mktime(datetime.strptime(x, "%d-%m-%Y %H:%M").timetuple()))).astype('int64')


# In[3]:


df_cleaned


# In[4]:


temp_series = df_cleaned.loc[df_cleaned['Register'] == "temperature"]
lid_series = df_cleaned.loc[df_cleaned['Register'] == "lid"]
tank_series = df_cleaned.loc[df_cleaned['Register'] == "operational"]
df_sorted = df_cleaned.sort_values(by=["Date"]).reset_index(drop=True)


# In[5]:


# with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
#     print(df_sorted)


# In[6]:


plt.figure(figsize=(20,10))
plt.plot(temp_series["Date"],temp_series["Value"])
plt.plot(lid_series["Date"],lid_series["Value"])
plt.plot(tank_series["Date"],tank_series["Value"])


# In[8]:


#create request test data
for index, row in df_sorted.iterrows():
    my_dict = {
        "request": {
        "identifier": "silo50",
        "data": {
          "variable": row[2],
          "unit": "celsius OR fahrenheit or state",
          "data_type": "real OR boolean",
          "timestamp": row[1],
          "value": row[0]
        }
      }
    }
    with open('./data/test_data/request_' + str(index) + '.json', 'w') as fp:
        json.dump(my_dict, fp)


json_list = os.listdir("./data/test_data/")
json_list.sort(key=lambda f: int(re.sub('\D', '', f)))
# for json in json_list:
#     print(json)


# In[9]:


#JSON TEMPLATES

#states json template
previous_state = {
  "tank": {
    "identifier": "",
    "timestamp": 0,
    "cfu": {
      "current_cfu": 0,
      "cfu_t0": 304750.0,
      "unit": "state",
      "data_type": "integer"
#       "value": "12"
    },
    "volume": {
      "unit": "",
      "milk": "",
      "data_type": "real",
      "value": 0,
    },
    "lid": {
      "unit": "state",
      "data_type": "boolean",
      "value": 0,
      "timestamp": 0
    },
    "operational": {
      "unit": "state",
      "data_type": "boolean",
      "value": 0,
      "timestamp": 0
    },
    "temperature": {
      "unit": "celsius OR fahrenheit",
      "data_type": "real",
      "value": 0,
      "timestamp": 0
    }
  }
}

#new request json template
# new_request={
#   "request": {
#     "identifier": "pagolekani",
#     "data": {
#       "variable": "temperature OR operational OR lid",
#       "unit": "celsius OR fahrenheit or state",
#       "data_type": "real OR boolean",
#       "timestamp": "unix_timestamp",
#       "value": "23.5 OR true OR false"
#     }
#   }
# }

#useful variables json template
useful_variables={
  "tank_turn_off_timestamp": 0,
    "tank_turn_on_timestamp": 0,
    "not_empty_tank_milk_inserted_timestamp":0
}


# In[10]:


#DECLARATION OF FUNCTIONS USED

def check_for_new_milk_in_NOT_empty_tank(prev_state, curr_state, new_request,useful_vars):
    result = False
    #tank must be operational so as to exists already milk
    if(curr_state["tank"]["operational"]["value"]==True):
        
        #extra check because it is possible for 2 consecutive temp requests the value to be rising. e.g.:
        #         653     2.3  1602653160  temperature
        #         654     1.0  1602653340          lid
        #         655     0.0  1602653400          lid
        #         656     5.5  1602653460  temperature
        #         657     7.2  1602653760  temperature
        #         658     1.0  1602653760  operational
        #         659     6.7  1602654060  temperature

        #At 656 new milk is inserted but at 657 the temp is still rising. This can be detected as a second insertion of milk which is wrong.
        #So we need to filter the first (and second) temp request that comes after the detected insertion which normally come in the next 5mins-10mins
        if((new_request["request"]["data"]["timestamp"] - useful_vars["not_empty_tank_milk_inserted_timestamp"]) > 600) :
            #check the new temperature is greater than that of the last measured
            if (new_request["request"]["data"]["value"]>curr_state["tank"]["temperature"]["value"]):
                #check if the new temperature is inside the limits 
                if (new_request["request"]["data"]["value"]>5 and new_request["request"]["data"]["value"]<15):
                    result = True
#     if result:
#         print("New milk added at NOT empty tank")
#         print(new_request["request"]["data"]["value"])
#         print(new_request["request"]["data"]["timestamp"])
#         print("--------------------------------------------------------")
#     else:
#         print("Quick check on milk")
    
    return result
            
def check_for_new_milk_in_empty_tank(prev_state, curr_state, new_request,useful_vars):
    result = False
    #check that the time of closed tank is big enough
    if((useful_vars["tank_turn_on_timestamp"] - useful_vars["tank_turn_off_timestamp"]) > 3600):
        #check if milk was added with a request within the first 5min of the operational turning True
        if((new_request["request"]["data"]["timestamp"] - useful_vars["tank_turn_on_timestamp"] ) < 100):
        
            #check the temperature is greater than a thershold
            if(new_request["request"]["data"]["value"]>15):
                result = True
        
#     if result:
#         print("New milk added at empty tank")
#         print(new_request["request"]["data"]["value"])
#         print(new_request["request"]["data"]["timestamp"])
#         print("--------------------------------------------------------")        
#     else:
#         print("Possible check on tank function")
    
    return result


#shift the states and create a new one (used for updating temperature,operational,lid)
def update_current_and_previous_status(prev_state,curr_state,new_request,idx):
    #shift the states backwards
    new_prev_state = curr_state
    #update the data of the correct variable and the timestamp (temperature,operational,lid)
    variable_to_be_updated = new_request["request"]["data"]["variable"]
    #deepcopy to avoid the refferences
    new_curr_state = copy.deepcopy(curr_state)
    #update the values
    new_curr_state["tank"][variable_to_be_updated]["unit"] = new_request["request"]["data"]["unit"]
    new_curr_state["tank"][variable_to_be_updated]["data_type"] = new_request["request"]["data"]["data_type"]
    new_curr_state["tank"][variable_to_be_updated]["value"] = new_request["request"]["data"]["value"]
    new_curr_state["tank"][variable_to_be_updated]["timestamp"] = new_request["request"]["data"]["timestamp"]
    new_curr_state["tank"]["timestamp"] = new_request["request"]["data"]["timestamp"]
    
    with open('./data/states_data/state_' + str(idx) + '.json', 'w') as fp:
        json.dump(new_curr_state, fp)
    
    return(new_prev_state,new_curr_state)



def predict_cfu(curr_state,new_request):
    temperatures_to_be_used = [curr_state["tank"]["temperature"]["value"],new_request["request"]["data"]["value"]]
    #check if there are missing temp values in order to interpolate from last value taken until now
    #if the interval between 2 temperature measures is greater than 9 min then interpolate the needed values
    if((new_request["request"]["data"]["timestamp"] - curr_state["tank"]["temperature"]["timestamp"]) > 540):
        #need interpolation
        values_need = len(list(range(curr_state["tank"]["temperature"]["timestamp"],new_request["request"]["data"]["timestamp"],300))) - 1 #excluding first value
        
        #adding the first and the last so as the function returns correct values
        temperatures_to_be_used = np.linspace(curr_state["tank"]["temperature"]["timestamp"],new_request["request"]["data"]["timestamp"],values_need + 2) 
    cfu = curr_state["tank"]["cfu"]["current_cfu"]
    for i in range(len(temperatures_to_be_used)-1):
        
        temp = (temperatures_to_be_used[i] + temperatures_to_be_used[i+1])/2
        base = 0.99290822 * cfu + 30251.23
        step = 0.99065815 * cfu + 20183.07
        rate = (step - cfu)/(base - cfu)
        new_cfu = cfu + (base - cfu) * rate**(math.log10(temp/10)/math.log10(0.7)) #
        cfu = new_cfu
        
        
    return cfu


# In[15]:


#TO DO
#READ CURR, PREV STATES AND GET NEW REQUEST FROM DATABASE


upd_cfu = False
milk_added_to_empty = []
milk_added_to_NOT_empty = []
my_cfu = []
my_idx = []
my_temp = []

current_state = copy.deepcopy(previous_state)
#inialization of states and useful_variables with manually created files
with open('./data/states_data/state_-2.json', 'w') as fp:
    json.dump(previous_state, fp)
with open('./data/states_data/state_-1.json', 'w') as fp:
    json.dump(current_state, fp)
with open('./data/states_data/useful_variables.json', 'w') as fp:
    json.dump(useful_variables, fp)
    
    
    
for idx,new_request in enumerate(json_list):

    #get the 2 previous states, the new request and the useful_variables
    with open('./data/states_data/state_' + str(idx-2) + '.json') as f:
        previous_state = json.load(f)
        
    with open('./data/states_data/state_' + str(idx-1) + '.json') as f:
        current_state = json.load(f)        
         
    with open('./data/test_data/' + new_request) as f:
        new_request = json.load(f)   
        
    with open('./data/states_data/useful_variables.json') as f:
        useful_vars = json.load(f)   
        
        
        
        
    #check if the request is a new temp or lid/operational state
    if (new_request["request"]["data"]["variable"]!="temperature"):
        #update the states
        update_current_and_previous_status(previous_state,current_state,new_request,idx)
        #save the the time of operational change from ON/OFF to OFF/ON
        if (new_request["request"]["data"]["variable"]=="operational"):
            
            if (new_request["request"]["data"]["value"]==False and current_state["tank"]["operational"]["value"]==True):
                
                useful_vars["tank_turn_off_timestamp"] = new_request["request"]["data"]["timestamp"]
                with open('./data/states_data/useful_variables.json', 'w') as fp:
                    json.dump(useful_vars, fp)
                    
            if (new_request["request"]["data"]["value"]==True and current_state["tank"]["operational"]["value"]==False):
                
                useful_vars["tank_turn_on_timestamp"] = new_request["request"]["data"]["timestamp"]
                with open('./data/states_data/useful_variables.json', 'w') as fp:
                    json.dump(useful_vars, fp)

    else:
        #check for outlier values of temperature sensors that are not positive and just replicate the current state as the new current state
        if(new_request["request"]["data"]["value"] <=0):
            with open('./data/states_data/state_' + str(idx) + '.json', 'w') as fp:
                json.dump(current_state, fp)            
            continue
            
        
        my_temp.append(new_request["request"]["data"]["value"])
        
        
        
        #check if any of the two events are valid
        empty_tank_milk_inserted = check_for_new_milk_in_empty_tank(previous_state,current_state,new_request,useful_vars) 
        not_empty_tank_milk_inserted = check_for_new_milk_in_NOT_empty_tank(previous_state,current_state,new_request,useful_vars)

        if empty_tank_milk_inserted:
            #set milk volume to the unit volume we have for that tank because only a unit was inserted (unit=standard quantity of milk per insertion)
            current_state["tank"]["volume"]["value"] = 1
            #set cfu to the initial calculated cfu_0
            current_state["tank"]["cfu"]["current_cfu"] = current_state["tank"]["cfu"]["cfu_t0"]
            cfu = current_state["tank"]["cfu"]["cfu_t0"]
            milk_added_to_empty.append(new_request["request"]["data"]["timestamp"])
            #calculate the cfu after inserting milk to empty tanke because we dont have cfu info in the ocassion that the tank already contains milk
            upd_cfu = True
            
            
        elif not_empty_tank_milk_inserted:
            #save the timestamp of the first detected milk insertion in NO empty tank
            useful_vars["not_empty_tank_milk_inserted_timestamp"] = new_request["request"]["data"]["timestamp"]
            with open('./data/states_data/useful_variables.json', 'w') as fp:
                json.dump(useful_vars, fp)            

            #get current volume and current cfu into variables for the equation to be more readable
            mv = current_state["tank"]["volume"]["value"]
            cfu_before_adding = current_state["tank"]["cfu"]["current_cfu"]
            
            #calculate new cfu based that the added milk has the constant initial cfu that is precalculated
            cfu = (mv*cfu_before_adding + current_state["tank"]["cfu"]["cfu_t0"])/(mv+1)
            current_state["tank"]["cfu"]["current_cfu"] = cfu
            
            #increase the current milk volume by one unit of milk volume
            current_state["tank"]["volume"]["value"] += 1
            milk_added_to_NOT_empty.append(new_request["request"]["data"]["timestamp"])
            
        else: 
            #predict cfu if we have inserted milk in empty tank
            if (upd_cfu == True):
                cfu = predict_cfu(current_state,new_request)
                current_state["tank"]["cfu"]["current_cfu"] = cfu

        
        if (upd_cfu == True):
            my_cfu.append(cfu)
            my_idx.append(idx)
        update_current_and_previous_status(previous_state,current_state,new_request,idx)
  
    


#TO DO
#SAVE CURR AND PREV STATES DATABASE CALS


# In[21]:


for date in milk_added_to_NOT_empty:
    print("Milk inserted to NON empty tank at: ", datetime.utcfromtimestamp(date).strftime('%H:%M:%S %d/%m/%Y'))
    
print()
for date in milk_added_to_empty:
    print("Milk inserted to empty tank at: ", datetime.utcfromtimestamp(date).strftime('%H:%M:%S %d/%m/%Y'))


# In[13]:


plt.figure(figsize=(10,5))
plt.grid()
# plt.ylim(0, 5)
plt.plot(my_idx,my_cfu)

plt.figure(figsize=(10,5))
# plt.ylim(0, 5)
plt.grid()
plt.plot(my_idx,my_temp[-len(my_idx):])

