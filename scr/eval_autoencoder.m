function [uu,vv,uv,CH,DB,clust,autoencoder,xtrain,xval,xtest] = eval_autoencoder(lvls,path)
    nc_lvls = ncread(path, 'num_metgrid_levels');
    blvls = ismember(nc_lvls,lvls);
    pos_lvls = find(blvls);
    uu =  ncread(path, 'UU');
    vv =  ncread(path, 'VV');
    u_size = size(uu);
    v_size = size(vv);
    uu = uu(:,:,pos_lvls,:);
    vv = vv(:,:,pos_lvls,:);
    uu = reshape(uu,[u_size(4),u_size(1)*u_size(2)*length(lvls)]);
    vv = reshape(vv,[v_size(4),v_size(1)*v_size(2)*length(lvls)]);
    uv = cat(2,uu,vv);
    disp(size(uv));
    [xtrain,xval,xtest] = dividerand(uv',0.2,0.2,0.6);
    disp(size(xtrain));
    autoencoder = trainAutoencoder(xtrain,100,'MaxEpoch',600);
    disp(size(xtest));
    uv_enc = encode(autoencoder,xtest);
    disp(size(uv_enc'));
    [CH,DB,clust] = kmeans_c(uv_enc');
end

function[CH, DB, clust] = kmeans_c(x)
    for i = 1:30
        clust(: , i) = kmeans(x, i, 'MaxIter', 1000);
        disp(i)
    end
    CH = evalclusters(x, clust, 'CalinskiHarabasz');
    DB = evalclusters(x, clust, 'DaviesBouldin');
end