import torch
import torch.nn as nn
from torchvision import models
import numpy as np
from gelsight_tb.models.modules.vgg_encoder import get_vgg_encoder
from gelsight_tb.models.model import Model


class PolicyNetwork(Model):

    def __init__(self, conf, load_resume=None):
        super(PolicyNetwork, self).__init__(conf, load_resume)
        self.batch_size = self.conf.batch_size
        self.loss = nn.MSELoss()

    def build_network(self):
        num_image_inputs = self.conf.num_image_inputs
        self.image_encoders = nn.ModuleList(
            [get_vgg_encoder(models.vgg13, self.conf.encoder_features) for _ in range(num_image_inputs)])
        current_layer_width = len(self.image_encoders) * self.conf.encoder_features + self.conf.state_dim
        self.fc_layers = nn.ModuleList()
        for layer in self.conf.policy_layers:
            self.fc_layers.append(nn.Linear(current_layer_width, layer))
            current_layer_width = layer
        self.output_layer = nn.Linear(current_layer_width, self.conf.action_dim)
        self.relu = torch.nn.ReLU()

    def forward(self, inputs):
        """
        :param inputs: a dictionary containing the following keys:
            'images': a list of num_cameras image tensors of shape [B, C, W, H]
            'state': a tensor of shape [B, state_dim]
        :return: a tensor of shape [B, action_dim]
        """

        image_inputs, state_input = inputs['images'], inputs['state']
        image_encodings = []
        for camera_i_images, encoder in zip(image_inputs, self.image_encoders):
            image_encodings.append(encoder(camera_i_images))
        image_encodings_cat = torch.cat(image_encodings, dim=1) # form [B, num_cam*encoder_features] tensor
        image_states_comb = torch.cat((image_encodings_cat, state_input), dim=1)
        output = image_states_comb
        for layer in self.fc_layers:
            output = self.relu(layer(output))
        output = self.output_layer(output)
        return output
