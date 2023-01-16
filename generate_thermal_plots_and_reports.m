function generate_thermal_plots_and_reports
% MATLAB script to manipulate MCC to generate thermal reports and plots
% without the user having to click on each one
%
% Update 05/04/2012
%
% I added the mups valves to the plot/text output.
%
% I removed code that used mcc_data.currentDir to look for the load name.
% This caused the load name to be incorrectly labeled when outputting
% propagated data to the review schedule directory after saving the
% propagation .mat file to this directory.
%
% I added a delay before saving each plot, since I found I had
% inadvertently saved other artifacts to the plots when it took too long to
% draw.
%
% - Matthew Dahmer
%
%
% Update 01/16/2023
%
% Added HRC CEA model, rearranged plot order
%
% - Matthew Dahmer
%


% List of views to plot, save a png image, and then save the text data
% and short names (for use in output filenames)
views_to_plot = {'Thermal Model (PLINE03T)',      'pline03t'
                 'Thermal Model (PLINE04T)',      'pline04t'
                 'Thermal Model (MUPS)',          'mups_valves'
                 'Thermal Model (Central Cyl)',   'tcylaft6'
                 'Thermal Model (Fwd Bulkhead)',  '4rt700t'
                 'Thermal Model (PFTANK2T)',      'pftank2t'
                 'Thermal Model (ACA)',           'aca'
                 'Thermal Model (1PDEAAT)',       '1pdeaat'
                 'Thermal Model (ACIS DPA)',      'dpa'
                 'Thermal Model (ACIS DEA)',      'dea'
                 'Thermal Model (ACIS FP)',       'acis_fp'
                 'Thermal Model (HRC CEA)',       '2ceahvpt'
};

             
% Directory to save the plot images and text files
if (ispc)
    start_dir = '\\noodle\GRETA\mission\Backstop';
else
    start_dir = '/home/mission/Backstop';
end
out_dir = uigetdir(start_dir, 'Select output directory');
if (isnumeric(out_dir))
    return
end

% Make the MCC figure handle visible
set(0,'showHiddenHandles','on');

% Get the handle to the MCC figure
h_fig = gcf; % Assuming it is the current figure

% Get the handles of the UI controls
handles = guihandles(h_fig);

% Get the list of views available in the view popupmenu
avail_views = get(handles.plotView,'string');

% Try to determine the name of the load
mcc_data = getappdata(h_fig,'MCCAppData');
loadname = '';
if (~isempty(mcc_data.bsfile))
    % Try getting the loadname from the backstop filename
    loadname = regexpi(mcc_data.bsfile,['mission[\\/]Backstop[\\/]'...
                   '([A-Z0-9]*)[\\/]CR[0-9_]*.backstop'],'tokens','once');
end
% Commented out since this causes more problems than it eliminates
% Better to just be explicit and allow the user to specify if not listed in
%  backstop file. 
%                         -Matt
%
%if (isempty(loadname) && ~isempty(mcc_data.currentDir))
%    % Try getting the loadname from the current directory
%    loadname = regexpi(mcc_data.currentDir,['mission[\\/]Backstop[\\/]'...
%                   '([A-Z0-9]*)[\\/]'],'tokens','once');
%end
if (isempty(loadname))
    % if no luck so far, just ask the user
    prompt = 'Enter the load name (for use in output filenames):';
    name = 'Enter Loadname';
    loadname = inputdlg(prompt, name);
end
if (iscell(loadname))
    loadname = loadname{1};
end

% Raise the MCC window to the top so screenshot capture it
figure(h_fig);
drawnow

% Loop through all the thermal plots
num_plots = 0;
for i=1:length(views_to_plot)
    this_view = views_to_plot{i,1};
    this_view_short_name = views_to_plot{i,2};
    
    % Get the index of this view in the view popupmenu
    this_view_ind = strmatch(this_view,avail_views,'exact');

    if ~isempty(this_view_ind)

        num_plots = num_plots + 1;

        % Select this view and execute the callback
        set(handles.plotView,'value',this_view_ind);
        disp(['Plotting ' this_view '...']);
        eval(get(handles.plotView,'callback'));
        drawnow;
        
        % I inserted a delay since the plotting can be slow and I've
        % inadvertently snapped partial windows. - Matt
        pause(1)
        
        % Save a snapshot of this plot
        [X,map] = getscreen(h_fig);

        % Save the snapshot to a file
        this_out_file = [loadname '_' this_view_short_name '.png'];
        disp(['   Saving plot snapshot to ' this_out_file '...']);
        if (isempty(map))
            imwrite(X,fullfile(out_dir,this_out_file),'png');
        else
            imwrite(X,map,fullfile(out_dir,this_out_file),'png');
        end
        
        % Save the data to a text file using plot2txt
        this_out_file = [loadname '_' this_view_short_name '_plot.txt'];
        disp(['   Writing data to text file ' this_out_file '...']);
        MCC('writePlot2TextFile',fullfile(out_dir,this_out_file));
    end
    
end

% Let the user know we're done
msgbox(['Finished plotting and outputting ' ...
         num2str(num_plots) ' views.']);


function [X,m]=getscreen(varargin)
%GETSCREEN replacement for GETFRAME for systems with multiple monitors. Use it just like you use GETFRAME.
%Can also be used to take screenshots of non-MATLAB windows. Requires JAVA.
%
%Calling options:
% Output X is m*n*3 cdata array. Output m is corresponding colormap (if applicable.)
% [X,m]=getscreen         Gets screenshot of current figure
% [X,m]=getscreen(h)      Gets screenshot of axes or figure with handle h
% [X,m]=getscreen(h,rect) Gets screenshot of at position rect relative to axes or figure with handle h.
% [X,m]=getscreen(rect) Gets screenshot of whatever is on your screen at position vector rect. (Relative to bottom left corner.)
%   rect is a 4 element position vector in pixel units, referenced from bottom left as usual for MATLAB.
%
% By Matt Daskilewicz <mattdaskil@gatech.edu> 11/2008
% www.asdl.gatech.edu
%


%process inputs:
if nargin==0
    h=gcf;
    rect=get(h,'position');
    rect(1:2)=[0 0];

elseif nargin==1
    if numel(varargin{1})==1 %it should be a handle
        h=varargin{1};
        if ~strcmp(get(h,'type'),'axes') && ~strcmp(get(h,'type'),'figure')
            error('First input must be a handle to an axes or figure, or a position vector');
        end

        rect = hgconvertunits(h, get(h,'position'), get(h,'units'), 'pixels', get(h,'parent')); %x/y coords of fighandle in pixels
        rect(1:2)=[1 1];

    elseif numel(varargin{1})==4 %it is a position vector
        h=[];
        rect=varargin{1};
    else % isnt a handle or a position vector
        error('First input must be a handle to an axes or figure, or a position vector');
    end

elseif nargin==2 %should be a handle and a position vector
    h=varargin{1};
    if ~ismember(get(h,'type'),{'figure';'axes'})
        error('First input must be a handle to an axes or figure, or a position vector');
    end

    rect=varargin{2};
    if length(rect)~=4
        error('Second input must be a 4 element position vector.')
    end

else
    error('Too many input arguments')
end


%get monitor resolutions... because java references coords from top of screen, need to know how big
%screens is.
monitorz=get(0,'monitorpositions');
maxheight=max(monitorz(:,4)); %max vertical resolution of all monitors

if ~isempty(h)

    %h is the handle to figure or axes whose origin (first 2 elemetns of position vector) we're taking
    %rect with respect to.
    origin=getpixelposition_mod(h,true);

    %if axes are in a uipanel, nudge rect slightly to account for panel border.
    if strcmp(get(get(h,'parent'),'type'),'uipanel')
        origin=origin+[1 1 0 0];
    end

    %also need position of the figure containing h, since origin is w.r.t this figure:
    fighandle = ancestor(h,'figure'); %handle of parent figure to h

    figorigin = hgconvertunits(fighandle, get(fighandle,'position'), get(fighandle,'units'), 'pixels', 0); %x/y coords of fighandle in pixels

    if strcmp(get(h,'type'),'figure')
        origin=[1 1 0 0]; %avoid double counting figorigin and origin if fighandle==h
    end


    % calculate dimensions of rectangle to take screenshot of: (in java coordinates)
    %java coordinates start at top left instead of bottom left, and start at [0,0]. Also "top" is defined as the top of your
    %largest monitor, even if that's not the one you're taking a screenshot from.

    x=figorigin(1)+origin(1)+rect(1)-3;
    y=maxheight-figorigin(2)-origin(2)-rect(2)-rect(4)+3;
    w=floor(rect(3));
    h=floor(rect(4));

    figure(fighandle); %make sure figure is visible on screen
    drawnow;

else %there is no figure... just take a screenshot of whatever's on the screen at rect

    rect=floor(rect);

    x=rect(1);
    y=rect(2); %maxheight-rect(2)-rect(4); %java coordinates start at top of screen.
    w=rect(3);
    h=rect(4);
end


% do java:
robo = java.awt.Robot;
target=java.awt.Rectangle(x,y,w,h);
image = robo.createScreenCapture(target); %take screenshot at rect
rasta=image.getRGB(0,0,w,h,[],0,w); %get RGB data from bufferedimage

%convert java color integers to matlab RGB format:
rasta=256^3+rasta;
B=uint8(mod(rasta,256));
G=uint8(mod((rasta-int32(B))./256,256));
R=uint8(mod((rasta-256*int32(G))./65536,256));

X.cdata=uint8(zeros(h,w,3));
X.cdata(:,:,1)=reshape(R,[w h])';
X.cdata(:,:,2)=reshape(G,[w h])';
X.cdata(:,:,3)=reshape(B,[w h])';
X.colormap=[];

if (nargout == 2)
    m=X.colormap;
    X=X.cdata;
end



function position = getpixelposition_mod(h,recursive)
% GETPIXELPOSITION Get position HG object in pixels.

% if recursive is true, the returned position is relative to the parent
% figure of H. Otherwise, it is relative to the parent of H.

% Copyright 1984-2004 The MathWorks, Inc.
% $Revision: 1.1.6.3 $ $Date: 2004/08/16 01:52:23 $

if nargin < 2
  recursive = false;
end

old_u = get(h,'Units');
set(h,'Units','pixels');
wasError = false;
try
  position = get(h,'Position');
catch
  wasError = true;
end
set(h,'Units',old_u);  
if wasError
  rethrow(lasterror);
end

parent = get(h,'Parent');
if recursive && ~isa(handle(parent),'figure')
 parentPos = [0 0];%getpixelposition(parent, recursive); 
 position = position + [parentPos(1) parentPos(2) 0 0];
end
  
