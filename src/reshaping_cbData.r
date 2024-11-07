#read all folders 
 dir.data <- "/home/milo/Documents/egtp/SISEPUEDE/COST_BENEFITS/refactorizacion/remote/cb_ssp_refac/output/"
 target_cb_file <- "cost_benefit_results.csv"
 cb_data <-read.csv(paste0(dir.data,target_cb_file))
 cb_chars <- data.frame(do.call(rbind, strsplit(as.character(cb_data$variable), ":")))
 colnames(cb_chars) <- c("name","sector","cb_type","item_1","item_2")
 cb_data <- cbind(cb_data,cb_chars)
 cb_data$value <- cb_data$value/1e6

#remove shifted 
 dim(cb_data)
 cb_data <- subset(cb_data,grepl("shifted",cb_data$item_2)==FALSE)
 dim(cb_data)
 ids <- unique(cb_data$variable)
 ids <- subset(ids,grepl("shifted2",ids)==FALSE)
#clean  
 cb_data <- subset(cb_data,grepl("shifted2",cb_data$variable)==FALSE)
 dim(cb_data)

#add Year 
cb_data$Year <- cb_data$time_period+2015

#change strategy names 
cb_data$strategy <- gsub("PFLO:UNCONSTRAINED", "Unconstrained Climate Action", cb_data$strategy )
cb_data$strategy <- gsub("PFLO:CONSTRAINED", "Constrained Climate Action-Efficiency Only", cb_data$strategy )
cb_data$strategy <- gsub("PFLO:TECHNOLOGICAL_ADOPTION", "Unconstrained Climate Action -Technology Adoption Scenario-", cb_data$strategy )

#create strategy id 
cb_data$strategy_id <- ifelse(cb_data$strategy=="Unconstrained Climate Action",6005,ifelse(cb_data$strategy=="Unconstrained Climate Action -Technology Adoption Scenario-",6004,6003))
cb_data$ids <- paste(cb_data$variable,cb_data$strategy_id,sep=":")

ids_all <- unique(cb_data$ids)

subset(ids_all,grepl("productivity",ids_all)==TRUE)


#edition to the table  
#differentiate between opex and capex 
cb_data$cb_type <- ifelse(cb_data$cb_type=="technical_cost" & cb_data$item_2=="opex","opex",cb_data$cb_type)
cb_data$cb_type <- ifelse(cb_data$cb_type=="technical_cost", "capex",cb_data$cb_type)


dir.out  <- "/home/milo/Documents/egtp/SISEPUEDE/COST_BENEFITS/refactorizacion/remote/cb_ssp_refac/output/"
write.csv(cb_data,paste0(dir.out,"cb_data.csv"),row.names=FALSE)



