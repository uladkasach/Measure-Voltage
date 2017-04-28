'''
cd /var/www/git/More/Measure-Voltage/2_analyze_data/; python3 analyze_voltage.py; 
'''
import numpy as np
import matplotlib.pyplot as plt

def main(target_file, RESISTOR, MIN_MAX_V, REJECT_OUTLIERS, EFFECTIVE_INDEX_SCALAR, AVERAGE_SET_SIZE, SLOPE_ZERO_WIDTH, LAST_MAX_EFFECTIVE_INDEX_SCALAR, LAST_MAX_AVERAGE_SIZE, LAST_MAX_ZERO_WIDTH,  BOOL_LOUD = False):
    ###########################
    ## 1) Read an input file and load it into pandas dataframe
    ###########################
    ## mean :  0.000, stdev :  0.000, reliability :    NAN, time : 583186820.000
    f = open(target_file, 'r');
    i = -1;
    means = [];
    stdev = [];
    reliability = [];
    time = [];
    for line in f.readlines():
        i += 1;
        line = "".join(line.split()); ## Remove all whitespace and newlines
        parts = line.split(",");
        if(len(parts) < 4): continue; ## sometimes first lines are not full data rows
        for a_part in parts:
            data = a_part.split(":");
            key = data[0];
            value = float(data[1]);
            if(key=="mean"): means.append(value);
            if(key=="stdev"): stdev.append(value);
            if(key=="reliability"): reliability.append(value);
            if(key=="time"): time.append(value);

    f.close();
    means = np.array(means);
    stdev = np.array(stdev);
    reliability = np.array(reliability);
    time = np.array(time);
    time = time - time[0]; ## Normalize time, make time start at 0;
    if(BOOL_LOUD): print(len(means));
    if(BOOL_LOUD): print(len(time));


    #############################
    ## 2) Plot it to see what we're working with
    #############################
    if(False):
        plt.scatter(time, means)
        plt.show()

    #############################
    ## 3) find each Discharge Cycle
    #############################
    ## Detect when voltage is constant, split data at those points
    def get_slope_type(average):
        zero_width = SLOPE_ZERO_WIDTH; ## If |average| < `zero_width` assume slope is 0 - tune this value by comparing number of split_indicies / value.
        if(average > 0 + zero_width): return 1;  ## Positive
        if(average < 0 - zero_width): return -1; ## Negative
        return 0;                                ## Zero
    def detect_change_indicies(means):
        ##########
        ## For each average consider X consecutive data points. Record when the slope changes between positive, 0, and negative. 
        ##########
        the_X = AVERAGE_SET_SIZE;
        split_indicies = [];
        change_type = [];
        #averages = [None] * the_X;
        averaging_set = [None] * the_X;
        average = None;
        difference = None;
        for index, this_mean in enumerate(means):
            averaging_set = averaging_set[1:];
            averaging_set.append(this_mean);
            #print(averaging_set);

            ## Check if we can calculate a new average
            if(None in averaging_set): continue;
            old_average = average;
            average = np.mean(np.array(averaging_set));

            ## Check if we can calculate difference between averages;
            if(old_average is None): continue;
            last_difference = difference;
            difference = average-old_average;

            ## Check if we can compare average slopes
            if(last_difference is None): 
                ## If its none, populate initial data
                split_indicies.append(0);
                change_type.append(get_slope_type(difference));
                continue;
            if(get_slope_type(difference) != get_slope_type(last_difference)):
                ## Record this as a split indicie, get the median index as the indicie
                effective_index = int(index - the_X*EFFECTIVE_INDEX_SCALAR); ## 5/6 is arbitrary constant to scale how far back in average to consider the start of this new slope
                split_indicies.append(effective_index);
                change_type.append(get_slope_type(difference));
                #print("Found at ", effective_index,  "Old: ", last_difference, " -vs- New: ", difference, " ->O: ", get_slope_type(last_difference), " ->N: ", get_slope_type(difference));

        return split_indicies, change_type;
    ###############
    ## Find where slope changes
    ###############
    split_indicies, change_type = detect_change_indicies(means);
    #print(len(split_indicies));
    #print(change_type);

    def find_discharge_windows(split_indicies, change_type):
        ## Discharge is characterized by the change from slope type of 0 to -1 and ends with the next 0.
        slopes = [None] * 3;
        indicies = [None] * 3;
        windows = [];
        for i in range(len(split_indicies)):
            this_index = split_indicies[i];
            this_change = change_type[i];

            ## Update slopes
            slopes = slopes[1:];
            slopes.append(this_change);
            indicies = indicies[1:];
            indicies.append(this_index);

            ## Detect pattern required for discharge
            if(slopes == [0, -1, 0]):
                ## record window
                windows.append([indicies[1], indicies[2]]);
        return windows;

    ###############
    ## Define all discharge windows
    ###############
    windows = find_discharge_windows(split_indicies, change_type);
    if(BOOL_LOUD): print(windows);

    #############################
    ## 4) Find tau for each discharge, V(tau) = 0.3697 * V_0
    ##############################
    def find_last_max_voltage_index(means):
        ## Given: Data starts at max and descends
        ## Approach, take average of LAST_MAX_AVERAGE_SIZE terms, detect when average starts dipping down
        averaging_set = [None] * LAST_MAX_AVERAGE_SIZE;
        average = None;
        difference = None;
        for index, this_mean in enumerate(means):
            averaging_set = averaging_set[1:];
            averaging_set.append(this_mean);
            #print(averaging_set);

            ## Check if we can calculate a new average
            if(None in averaging_set): continue;
            old_average = average;
            average = np.mean(np.array(averaging_set));

            ## Check if we can calculate difference between averages;
            if(old_average is None): continue;
            difference = average-old_average;
            
            if(difference < 0 - LAST_MAX_ZERO_WIDTH):
                effective_index = int(index - LAST_MAX_AVERAGE_SIZE*LAST_MAX_EFFECTIVE_INDEX_SCALAR); ## 5/6 is arbitrary constant to scale how far back in average to consider the start of this new slope
                return effective_index;
            return None;
            
            
        
    def detect_tau_from_window(window, means, time):
        these_means = means[window[0]:window[1]];
        max_voltage = np.amax(these_means);
        if(max_voltage < MIN_MAX_V): return None;
        
        ## Find position of last max voltage
        ##      note, we can have 4.76, 4.78, 4.77, 4.78, 4.76, ....
        new_beginning_index = find_last_max_voltage_index(these_means);
        if(new_beginning_index is None): return None; ## If decay was not big enough to be found.
        #print(these_means);
        #print("NBI:", new_beginning_index);
        window[0] = window[0] + new_beginning_index;
        
        ## Update Window
        these_means = means[window[0]:window[1]];
        these_times = time[window[0]:window[1]];
        these_times = these_times - these_times[0]; ## scale time to be zero at first time.
        
        ## Calc Max and Target Voltage
        max_voltage = np.amax(these_means);
        if(max_voltage < MIN_MAX_V): return None;
        target_voltage = max_voltage*0.367879441; ## = V_0 * e^{-1}

        ## Find where voltage becomes less than or equal to target voltage. 
        ##      Because we are not likely to find exact target voltage, we wont find exact target time.
        ##      Assume that slope is linear, y = mx+b = target_v = ((this_mean - last_mean)/2) * x + last_mean 
        ##                                            -> x = 2*(target_v - last_mean)/(this_mean - last_mean);
        ##                                            -> target_t =  ((this_time - last_time)/2)*x + last_time;
        last_mean = 0;
        last_time = 0;
        target_time = None;
        for i in range(len(these_means)):
            this_mean = these_means[i];
            this_time = these_times[i];

            if(this_mean <= target_voltage):
                x = 2 * (target_voltage - last_mean) / (this_mean - last_mean);
                target_time = ((this_time - last_time)/2)*x + last_time;
                break;

            last_mean = this_mean;
            last_time = this_time;

        ## Ensure target voltage was found
        if(target_time is None): return None;       

        '''
        print("tv:", target_voltage);
        print("lm:", last_mean);
        print("lt:", last_time);
        print("tm:", this_mean);
        print("tt:", this_time);
        '''
        if(BOOL_LOUD): print("mv:", max_voltage);
        #print("tv:", target_voltage);

        #print(this_time);
        #print(target_time);
        assume_linear = True;
        if(assume_linear == True):
            return target_time;
        else:
            return this_time;

    tau_list = [];
    non_compute = 0;
    for window in windows:
        tau = detect_tau_from_window(window, means, time);
        if(tau == None):
            non_compute += 1;
            #print("Tau is not computable for window ", window);
            continue;
        tau_list.append(tau);
    tau_list = np.array(tau_list);
    print(tau_list);
    print("Non Computable: ", non_compute);

    ##############################
    ## 5) Statistically analyze each discharge
    ##############################
    def reject_outliers(data, m=2):
        return data[abs(data - np.mean(data)) < m * np.std(data)]
    if(REJECT_OUTLIERS == True):
        rejected_points = len(tau_list);
        tau_list = reject_outliers(tau_list);
        rejected_points = rejected_points - len(tau_list);
        print("Rejected Points: ", rejected_points);

    used_data_points = len(tau_list);
    print("Data Points: ", used_data_points);


    tau_list = tau_list * 10**(-6); ## Convert to seconds
    tau_mean = np.mean(tau_list);
    tau_std = np.std(tau_list);
    print("Tau Mean : ", tau_mean);
    print("Tau Std : ", tau_std);

    if(RESISTOR == 1): R = 2.8 * 10**6;
    if(RESISTOR == 2): R = 5.65 * 10**6;
    print(" Mean C ", tau_mean / R);
    print(" Std C ", tau_std / R);
    
    return used_data_points;

if __name__ == "__main__":
    
    ###########################
    ## User Inputs
    ###########################
    target_file = "../1_record_data/results/" + "3pf_R2_semicardboard.txt";
    RESISTOR = 2;
    EFFECTIVE_INDEX_SCALAR = 0.3;           ## Move this around to maximize the amount of computable points
    AVERAGE_SET_SIZE = 10;                  ## See above
    SLOPE_ZERO_WIDTH = 0.1                  ## ""
    
    LAST_MAX_AVERAGE_SIZE = 3;              ## Move this around to minimize the time between max and target
    LAST_MAX_ZERO_WIDTH = 0.1;              ## "". Note, if too large then error will be thrown because decay was not found.
    LAST_MAX_EFFECTIVE_INDEX_SCALAR = 1;    ## "". Keep at one. Tune Zero width instead..
               
    MIN_MAX_V = 4.6;                        ## Choose the minimum max_voltage to be considered as the start of a discharge
    REJECT_OUTLIERS = True;                 ## Reject outliers by standard deviation > 2 or not
    
    statistic_goal = "MAX";                 ## Gridsearch Optimization Method;
                                            ##      Note, the data returned by main() needs to be hardcoded if changing the gridsearch goal

    ########
    ## Run grid search on data, minimize non_computable
    ########
    EFFECTIVE_INDEX_SCALAR = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9];
    AVERAGE_SET_SIZE = [10, 20, 30, 40];
    if(statistic_goal == "MAX"): best_statistic = 0;
    if(statistic_goal == "MIN"): best_statistic = 99999999999;
    best_set = None;
    for this_effective_index_scalar in EFFECTIVE_INDEX_SCALAR:
        for this_average_set_size in AVERAGE_SET_SIZE:
            this_statistic = main(target_file, RESISTOR, MIN_MAX_V, REJECT_OUTLIERS, this_effective_index_scalar, this_average_set_size, SLOPE_ZERO_WIDTH, LAST_MAX_EFFECTIVE_INDEX_SCALAR, LAST_MAX_AVERAGE_SIZE, LAST_MAX_ZERO_WIDTH);
            if((statistic_goal == "MIN" and this_statistic < best_statistic) or (statistic_goal == "MAX" and this_statistic > best_statistic)):
                best_statistic = this_statistic;
                best_set = [this_effective_index_scalar, this_average_set_size];
                
    #########
    ## Run it
    #########
    main(target_file, RESISTOR, MIN_MAX_V, REJECT_OUTLIERS, best_set[0], best_set[1], SLOPE_ZERO_WIDTH, LAST_MAX_EFFECTIVE_INDEX_SCALAR, LAST_MAX_AVERAGE_SIZE, LAST_MAX_ZERO_WIDTH);
    print("min_set ", best_set);
    