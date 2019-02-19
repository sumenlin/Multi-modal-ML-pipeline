#!/usr/bin/python
# encoding=utf8
'''
Tagets: 
feature engineering
1) feature extraction:time series
2) PCA 
3) feature selection
'''
import pandas as pd 
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from scipy.stats import pearsonr

#feature extraction
def featureExtraction(data,identification,featureList=None,statis = ['mean','std','median','max','min']):
    """Extract statistics of time series features, including mean, median, max, min and standard deviance.
    
    :param data: data input
    :type data: data frame
    :param identification: identification for each subject in data set
    :type identification: string
    :param featureList: the list of feature names for statistics extraction. If ``None``, all features in the data will be used for extraction.
    :type featureList: list (default=None)
    :param statis: statistics to be extracted.
                           if ``mean``, compute the mean along each feature for each subject;
                           if ``std``, compute the standard deviance along each feature for each subject;
                           if ``median``, compute the median along each feature for each subject;
                           if ``max``, compute the max value along each feature for each subject;
                           if ``min``, compute the min value along each feature for each subject;
                           all can only be used for numeric data.
    :type statis: int, str, optional (default=['mean','std','median','max','min'])
    :returns: data after adding the extracted statistics
    :rtype: data frame
    """
    nx = [identification]
    if featureList==None:
        featureList = list(set(data.columns.tolist())-set([identification]))
    for x in featureList:
        if 'mean' in statis:
            df = data.groupby(identification)[x].mean().reset_index()
            df = df.rename(index=str,columns={x:x+"_mean"})
            data = pd.merge(df,data,on=identification,how='right')
            nx.append(x+"_mean")
        if 'std' in statis:
            df = data.groupby(identification)[x].std().reset_index()
            df = df.rename(index=str,columns={x:x+"_std"})
            data = pd.merge(df,data,on=identification,how='right')
            nx.append(x+"_std")
        if 'median' in statis:
            df = data.groupby(identification)[x].median().reset_index()
            df = df.rename(index=str,columns={x:x+"_median"})
            data = pd.merge(df,data,on=identification,how='right')
            nx.append(x+"_median")
        if 'max' in statis:
            df = data.groupby(identification)[x].max().reset_index()
            df = df.rename(index=str,columns={x:x+"_max"})
            data = pd.merge(df,data,on=identification,how='right')
            nx.append(x+"_max")
        if 'min' in statis:
            df = data.groupby(identification)[x].min().reset_index()
            df = df.rename(index=str,columns={x:x+"_min"})
            data = pd.merge(df,data,on=identification,how='right')
            nx.append(x+"_min")
    data = data.ix[:,nx]
    return data

#PCA 
def featurePCA(data_train,data_test,pca_number = 3,random_state = 40):
    """Performe PCA analysis on data.
    
    :param data_train: training data
    :type data_train: data frame
    :param data_test: testing data
    :type data_test: data frame
    :param pca_number: the number of PCA components
    :type pca_number: int (default=3)
    :param random_state: the seed of the pseudo random number generator to use if applicable.
    :type random_state: int (default=40)
    :returns: data after PCA analysis
    :rtype: data frame
    """
    pca = PCA(n_components=pca_number, random_state=random_state).fit(data_train)
    data_train_pca = pca.transform(data_train)
    data_test_pca = pca.transform(data_test)
    return data_train_pca,data_test_pca


#feature selection on training data
def selectFeature(data,target, kind = 'all',co_linear = False,N = None):
    """Performe feature selection on data.
    
    :param data: features
    :type data: data frame
    :param target: ground truth data
    :type target: data series
    :param kind: the strategy for feature selection. If ``correlation``, use Pearson correlation coefficients as metric for feature selection; 
                 if ``linear``, use coefficients from linear LinearR egression as metric for feature selection; 
                 if ``all``, include selected features from both Pearson correlation and regression coefficients. 
    :type kind: string (default='all')
    :param N: the number of features to select. If ``None``, select the top ``N`` features where ``N`` is from 5 to the number of total features with interval 5.  
    :type N: int (default=None)
    :param co_linear: indicator if eliminating the features with high correlation for each other. 
    :type co_linear: bool (default=False)
    :returns: list of potential selected feature lists
    :rtype: list of list
    """
    M = int((len(data.index))**(0.5))
    if N==None:
        N = min(len(data.columns.tolist()),M)
        LN = range(5,N+1,5)
    elif type(N)==int:
        LN = [N]
    elif type(N)==list:
        LN = N

    Xheads = data.columns.tolist()
    Xheads_list = []
    df = pd.DataFrame()
    df['Xheads'] = Xheads
    if kind == 'correlation' or kind == 'all':
    # correlation selection
        corrs = []
        d1 = y.tolist()
        for xhead in Xheads:
            # print xhead
            # d1 = data[yhead].tolist()
            d2 = data[xhead].tolist()
            corr = pearsonr(d1,d2)
            corrs.append(corr[0])
            # corrs.append(abs(corr[0]))
        df['correlation'] = corrs
        df = df.sort_values(by='correlation', ascending=False).reset_index(drop=True)
        if not co_linear:
            for n in LN:
                Xheads_new = df.Xheads.tolist()[:n]
                Xheads_list.append(Xheads_new)
        else:
            tmp_x = []
            tmp = 0
            Xheads_new = df.Xheads.tolist()
            while tmp<len(Xheads_new) and len(tmp_x)<LN[-1]:
                d1 = data[Xheads_new[tmp]].tolist()
                for tx in tmp_x:
                    d2 = data[tx].tolist()
                    if pearsonr(d1,d2)[0]>0.5:
                        break
                else:
                    tmp_x.append(Xheads_new[tmp])
                    if len(tmp_x) in LN:
                        Xheads_list.append(tmp_x)
                tmp += 1

    #linear
    if kind == 'linear' or kind == 'all':
        X = data
        Y = y
        lr = LinearRegression()  
        lr.fit(X, Y)
        df['lr_coeff'] = lr.coef_.tolist()
        df = df.sort_values(by='lr_coeff', ascending=False).reset_index(drop=True)
        # for n in LN:
        #     Xheads_new = df.Xheads.tolist()[:n]
        #     Xheads_list.append(Xheads_new)

        if not co_linear:
            for n in LN:
                Xheads_new = df.Xheads.tolist()[:n]
                Xheads_list.append(Xheads_new)
        else:
            tmp_x = []
            tmp = 0
            Xheads_new = df.Xheads.tolist()
            while tmp<len(Xheads_new) and len(tmp_x)<LN[-1]:
                d1 = data[Xheads_new[tmp]].tolist()
                for tx in tmp_x:
                    d2 = data[tx].tolist()
                    if pearsonr(d1,d2)[0]>0.5:
                        break
                else:
                    tmp_x.append(Xheads_new[tmp])
                    if len(tmp_x) in LN:
                        Xheads_list.append(tmp_x)
                tmp += 1

    return Xheads_list

